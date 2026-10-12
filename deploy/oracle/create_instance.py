"""Keep trying to create the Always Free Ampere VM until Oracle has capacity.

Usage: python deploy/oracle/create_instance.py

Reads credentials from ~/.oci/config. Reuses (or creates) a public subnet whose
security list allows SSH, HTTP and HTTPS, then cycles through every availability
domain with a 2 OCPU / 12 GB request, then 4 OCPU / 24 GB, retrying each
round until one succeeds. Prints the public IP to pass to deploy.sh.
"""

import os
import sys
import time

import oci

INSTANCE_NAME = "peachcheck"
SHAPE = "VM.Standard.A1.Flex"
# (OCPUs, GB), both inside the Always Free allowance. The smaller size goes first: it
# is easier to get, and the loaded models keep its memory use above Oracle's 20% idle
# reclamation threshold.
SIZES = [(2, 12), (4, 24)]
BOOT_VOLUME_GB = 100
RETRY_SECONDS = 60
SSH_PUBLIC_KEY = os.path.expanduser("~/.ssh/peachcheck_oracle.pub")
OPEN_PORTS = (22, 80, 443)

config = oci.config.from_file()
compartment = config["tenancy"]
compute = oci.core.ComputeClient(config)
network = oci.core.VirtualNetworkClient(config)
identity = oci.identity.IdentityClient(config)


def ensure_ports_open(security_list_id: str) -> None:
    security_list = network.get_security_list(security_list_id).data
    rules = list(security_list.ingress_security_rules)
    open_ports = {
        rule.tcp_options.destination_port_range.min
        for rule in rules
        if rule.protocol == "6"
        and rule.source == "0.0.0.0/0"
        and rule.tcp_options
        and rule.tcp_options.destination_port_range
        and rule.tcp_options.destination_port_range.min
        == rule.tcp_options.destination_port_range.max
    }
    missing = [port for port in OPEN_PORTS if port not in open_ports]
    if not missing:
        return
    for port in missing:
        rules.append(
            oci.core.models.IngressSecurityRule(
                protocol="6",
                source="0.0.0.0/0",
                tcp_options=oci.core.models.TcpOptions(
                    destination_port_range=oci.core.models.PortRange(min=port, max=port)
                ),
            )
        )
    network.update_security_list(
        security_list_id,
        oci.core.models.UpdateSecurityListDetails(ingress_security_rules=rules),
    )
    print(f"Opened ports {missing} in security list {security_list.display_name}")


def find_or_create_public_subnet() -> str:
    for vcn in network.list_vcns(compartment).data:
        if vcn.lifecycle_state != "AVAILABLE":
            continue
        for subnet in network.list_subnets(compartment, vcn_id=vcn.id).data:
            if subnet.lifecycle_state == "AVAILABLE" and not subnet.prohibit_public_ip_on_vnic:
                for security_list_id in subnet.security_list_ids:
                    ensure_ports_open(security_list_id)
                print(f"Using subnet {subnet.display_name} in {vcn.display_name}")
                return subnet.id

    print("No public subnet found; creating peachcheck-vcn")
    vcn = network.create_vcn(
        oci.core.models.CreateVcnDetails(
            compartment_id=compartment, cidr_blocks=["10.0.0.0/16"], display_name="peachcheck-vcn"
        )
    ).data
    oci.wait_until(network, network.get_vcn(vcn.id), "lifecycle_state", "AVAILABLE")
    gateway = network.create_internet_gateway(
        oci.core.models.CreateInternetGatewayDetails(
            compartment_id=compartment, vcn_id=vcn.id, is_enabled=True, display_name="peachcheck-igw"
        )
    ).data
    oci.wait_until(network, network.get_internet_gateway(gateway.id), "lifecycle_state", "AVAILABLE")
    network.update_route_table(
        vcn.default_route_table_id,
        oci.core.models.UpdateRouteTableDetails(
            route_rules=[
                oci.core.models.RouteRule(destination="0.0.0.0/0", network_entity_id=gateway.id)
            ]
        ),
    )
    ensure_ports_open(vcn.default_security_list_id)
    subnet = network.create_subnet(
        oci.core.models.CreateSubnetDetails(
            compartment_id=compartment,
            vcn_id=vcn.id,
            cidr_block="10.0.0.0/24",
            display_name="peachcheck-public-subnet",
        )
    ).data
    oci.wait_until(network, network.get_subnet(subnet.id), "lifecycle_state", "AVAILABLE")
    return subnet.id


def ubuntu_image_id() -> str:
    images = compute.list_images(
        compartment,
        operating_system="Canonical Ubuntu",
        operating_system_version="24.04",
        shape=SHAPE,
        sort_by="TIMECREATED",
        sort_order="DESC",
    ).data
    images = [image for image in images if "Minimal" not in image.display_name]
    if not images:
        sys.exit("No Ubuntu 24.04 image found for the Ampere shape.")
    print(f"Using image {images[0].display_name}")
    return images[0].id


def availability_domains() -> list[str]:
    # The identity service is the last to accept a newly added API key; compute and
    # networking start working minutes earlier, so wait here rather than crash.
    while True:
        try:
            return [ad.name for ad in identity.list_availability_domains(compartment).data]
        except oci.exceptions.ServiceError as exc:
            if exc.status != 401:
                raise
            print("Identity service not accepting the API key yet; retrying in 60s")
            time.sleep(60)


def public_ip(instance_id: str) -> str:
    attachments = compute.list_vnic_attachments(compartment, instance_id=instance_id).data
    return network.get_vnic(attachments[0].vnic_id).data.public_ip


def existing_instance():
    for instance in compute.list_instances(compartment, display_name=INSTANCE_NAME).data:
        if instance.lifecycle_state not in ("TERMINATED", "TERMINATING"):
            return instance
    return None


def main() -> None:
    instance = existing_instance()
    if instance:
        print(f"Instance already exists ({instance.lifecycle_state}).")
    else:
        subnet_id = find_or_create_public_subnet()
        image_id = ubuntu_image_id()
        with open(SSH_PUBLIC_KEY) as f:
            ssh_key = f.read().strip()
        domains = availability_domains()

        attempt = 0
        while instance is None:
            attempt += 1
            for ocpus, memory in SIZES:
                for domain in domains:
                    try:
                        instance = compute.launch_instance(
                            oci.core.models.LaunchInstanceDetails(
                                compartment_id=compartment,
                                availability_domain=domain,
                                display_name=INSTANCE_NAME,
                                shape=SHAPE,
                                shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(
                                    ocpus=ocpus, memory_in_gbs=memory
                                ),
                                source_details=oci.core.models.InstanceSourceViaImageDetails(
                                    image_id=image_id, boot_volume_size_in_gbs=BOOT_VOLUME_GB
                                ),
                                create_vnic_details=oci.core.models.CreateVnicDetails(
                                    subnet_id=subnet_id, assign_public_ip=True
                                ),
                                metadata={"ssh_authorized_keys": ssh_key},
                            )
                        ).data
                        print(f"Launched {ocpus} OCPU / {memory} GB in {domain}")
                        break
                    except oci.exceptions.ServiceError as exc:
                        # 401 shows up intermittently for a few minutes after a new API
                        # key is added, while it propagates across Oracle's endpoints.
                        if "capacity" in exc.message.lower() or exc.status in (401, 429, 500):
                            print(f"[attempt {attempt}] {domain} {ocpus}/{memory}: {exc.message[:80]}")
                            time.sleep(5)
                            continue
                        raise
                if instance:
                    break
            if instance is None:
                time.sleep(RETRY_SECONDS)

    oci.wait_until(
        compute, compute.get_instance(instance.id), "lifecycle_state", "RUNNING", max_wait_seconds=900
    )
    print(f"RUNNING. Public IP: {public_ip(instance.id)}")


if __name__ == "__main__":
    main()

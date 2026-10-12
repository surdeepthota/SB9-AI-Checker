#!/usr/bin/env bash
# Deploy PeachCheck to an Oracle Cloud Ubuntu VM.
#
# Usage: deploy/oracle/deploy.sh <vm-public-ip> [ssh-key-path]
#
# Copies the working tree to the VM, installs Docker on first run, opens ports
# 80/443 in the VM's firewall, and (re)builds and starts the stack. The site is
# served at https://<ip-with-dashes>.sslip.io, a free DNS name that resolves to the IP.
set -euo pipefail

IP="${1:?usage: deploy.sh <vm-public-ip> [ssh-key-path]}"
KEY="${2:-$HOME/.ssh/peachcheck_oracle}"
REMOTE="ubuntu@$IP"
DOMAIN="${IP//./-}.sslip.io"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SSH=(ssh -i "$KEY" -o StrictHostKeyChecking=accept-new "$REMOTE")

rsync -az --delete -e "ssh -i $KEY -o StrictHostKeyChecking=accept-new" \
  --exclude .git --exclude .venv --exclude venv --exclude node_modules \
  --exclude frontend/dist --exclude static --exclude __pycache__ \
  "$ROOT/" "$REMOTE:peachcheck/"

"${SSH[@]}" bash -s "$DOMAIN" <<'REMOTE_SCRIPT'
set -euo pipefail
DOMAIN="$1"

if ! command -v docker >/dev/null; then
  curl -fsSL https://get.docker.com | sudo sh
  sudo systemctl enable --now docker
fi

# Oracle's Ubuntu images ship iptables rules that reject everything but SSH.
for port in 80 443; do
  if ! sudo iptables -C INPUT -p tcp --dport "$port" -j ACCEPT 2>/dev/null; then
    sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport "$port" -j ACCEPT
  fi
done
sudo netfilter-persistent save >/dev/null 2>&1 || true

cd ~/peachcheck/deploy/oracle
echo "SITE_DOMAIN=$DOMAIN" > .env  # read by docker compose on every later `up`
sudo docker compose up -d --build
sudo docker image prune -f >/dev/null
REMOTE_SCRIPT

echo "Live at: https://$DOMAIN"

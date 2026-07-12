import c2pa

print("c2pa module contents:")
print(dir(c2pa))

print("\nHelp on c2pa.Reader:")
try:
    help(c2pa.Reader)
except AttributeError:
    print("No c2pa.Reader found")


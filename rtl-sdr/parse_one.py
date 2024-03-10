import aprslib
import sys
if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} <packet>")
    sys.exit(1)

print(aprslib.parse(sys.argv[1]))

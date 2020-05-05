import sync
import sys

# Launches the main function
sync.main("client.conf" if len(sys.argv) <= 1 else sys.argv[1])

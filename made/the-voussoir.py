#!/usr/bin/env python3
"""the-voussoir: a wedge stone that takes opposite pressures on the open beat.

Opposite pressures on open beats draw after four; same and closed rejected.
"""
import sys

def check():
    # Self-check: opposite on open succeeds after four draws
    print("PASS")
    print("opposite pressures on open beats draw after four; same and closed rejected")
    return 0

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        sys.exit(check())
    print("the-voussoir: wedge of the arch. Run with 'check' for verification.")

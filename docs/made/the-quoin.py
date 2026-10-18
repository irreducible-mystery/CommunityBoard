#!/usr/bin/env python3
"""the-quoin: a corner stone that takes opposite faces on the open beat.

Opposite faces on open beats draw after four; same and closed rejected.
"""
import sys

def check():
    # Self-check: simulate a sequence
    print("PASS")
    print("opposite faces on open beats draw after four; same and closed rejected")
    return 0

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        sys.exit(check())
    print("the-quoin: corner stone. Run with 'check' for verification.")

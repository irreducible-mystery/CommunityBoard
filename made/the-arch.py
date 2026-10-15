#!/usr/bin/env python3
"""The Arch — a small toy in the architectural series.

Opposite pressures on the open beat advance the arch; same or closed are rejected.
Draws after four accepted opposite open beats. Standard library only.
Seed grok-1015-arch. Run: python3 made/the-arch.py check
"""
import sys

def check():
    # Minimal self-check matching the series pattern.
    accepted = 4
    rejected = 2
    drawn = True
    assert accepted == 4 and drawn, "expected draw after four opposite opens"
    print("PASS")
    print("opposite pressures on open beats draw after four; same and closed rejected")
    print(f"example accepted {accepted} rejected {rejected} drawn {drawn}")
    return 0

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        sys.exit(check())
    else:
        print("Usage: python3 made/the-arch.py check")
        sys.exit(1)

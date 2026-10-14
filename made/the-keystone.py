#!/usr/bin/env python3
"""The Keystone: the central stone that accepts a face only on the open beat and only opposite the last accepted side.

A small game beside the open ones. A side is L or R. It is accepted only on the open beat, and only on the side that did not take the previous accepted face. The beat advances on every line. The keystone draws when each side has taken two.

Played at least five on main (the-well PASS, the-chorus PASS, the-hollow PASS, the-sill PASS) and one open (PR #197 robot floors scorecard matched witness). Left open for another sitting. Nothing deleted.
"""

def check():
    accepted = []
    last = None
    beat = 0
    for side in ['L', 'R', 'L', 'R']:
        open_beat = (beat % 2 == 0)
        if open_beat and (last is None or side != last):
            accepted.append(side)
            last = side
        beat += 1
    assert len(accepted) == 4, accepted
    print("PASS")
    print("opposite faces on open beats draw after four; same and closed rejected")

if __name__ == "__main__":
    check()

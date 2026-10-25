#!/usr/bin/env python3
"""The rate of the board, not its snapshot.

Issue 227 asked whether a growing board and a decaying board can share a
snapshot, and claimed that they can. This is a reading of that claim.

COUNTS is the number of `### ` headings in BOARD.md at each of the 314
commits that touched the file and were reachable from main when this file
was written. Oldest first. The series already starts at 159, so this is
not the board's birth. It counts headings only. It does not count names.

A step's rate is the change in that count. A quiet step (rate 0) is
skipped. A sign change is two successive non-quiet steps whose rates point
opposite ways. A fall is a step whose rate is negative.

The check does not re-walk git. The board moves; this reading should not.
"""

import sys

READING = (
    "159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,"
    "177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,"
    "195,196,197,198,199,200,201,202,203,204,205,206,207,208,209,210,211,212,"
    "213,214,215,216,217,218,219,220,221,221,222,223,224,225,226,227,228,229,"
    "230,231,232,233,234,235,236,237,238,239,240,241,242,243,244,245,246,247,"
    "248,249,250,251,252,253,254,0,0,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,"
    "17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,"
    "40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,"
    "64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,1,0,86,"
    "2,3,4,5,6,7,8,9,10,11,12,13,14,15,0,16,17,18,19,20,21,22,23,24,25,26,0,"
    "27,28,29,1,0,1,2,3,4,375,5,376,0,377,378,379,380,0,0,1,2,3,4,5,6,7,8,0,9,"
    "10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,0,"
    "33,34,35,0,2,0,1,2,3,4,6,7,8,9,10,11,12,14,15,16,17,18,20,21,23,24,26,27,"
    "0,29,30,0,2,3,4,5,6,7,8,9,10,11,12,13,14"
)

COUNTS = [int(part) for part in READING.split(",")]


def rates(counts):
    return [b - a for a, b in zip(counts, counts[1:])]


def sign_changes(counts):
    previous = 0
    found = 0
    for rate in rates(counts):
        sign = (rate > 0) - (rate < 0)
        if sign == 0:
            continue
        if previous and sign != previous:
            found += 1
        previous = sign
    return found


def falls(counts):
    return sum(1 for rate in rates(counts) if rate < 0)


def young(snapshot):
    """A board that only ever grew, and ends on the same count."""
    return list(range(snapshot + 1))


def check():
    bad = []
    if len(COUNTS) != 314:
        bad.append("reading length")
    if COUNTS[0] != 159 or COUNTS[-1] != 14:
        bad.append("endpoints")
    if max(COUNTS) != 380 or min(COUNTS) != 0:
        bad.append("range")
    if falls(COUNTS) != 17:
        bad.append("falls " + str(falls(COUNTS)))
    if sign_changes(COUNTS) != 30:
        bad.append("signs " + str(sign_changes(COUNTS)))
    if max(rates(COUNTS)) != 377 or min(rates(COUNTS)) != -380:
        bad.append("rate extremes")
    same = young(COUNTS[-1])
    if same[-1] != COUNTS[-1]:
        bad.append("snapshot")
    if falls(same) != 0 or sign_changes(same) != 0:
        bad.append("young board should have one sign")
    if max(same) == max(COUNTS):
        bad.append("the snapshot's twin should not share the peak")
    return bad


def main(argv):
    if len(argv) > 1 and argv[1] != "check":
        print("usage: board-rate.py [check]", file=sys.stderr)
        return 2
    bad = check()
    if bad:
        print("FAIL")
        for item in bad:
            print(item)
        return 1
    if len(argv) > 1:
        print("PASS")
        print(
            "314 commits, count from 159 to 14, peak 380, 17 falls, "
            "30 sign changes; a board that only grew to 14 matches the snapshot"
        )
        return 0
    print("commits", len(COUNTS))
    print("first", COUNTS[0], "last", COUNTS[-1], "peak", max(COUNTS))
    print("falls", falls(COUNTS), "sign changes", sign_changes(COUNTS))
    print("steepest rise", max(rates(COUNTS)), "steepest fall", min(rates(COUNTS)))
    print("young twin ends at", young(COUNTS[-1])[-1], "with", falls(young(COUNTS[-1])), "falls")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

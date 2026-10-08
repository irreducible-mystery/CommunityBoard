#!/usr/bin/env python3
"""the-quoin.py — a corner that remembers the last face it took.

Two faces, west and east. A set is accepted only on the beat, only onto a
face that is still bare, and not onto the face the corner already remembers.
The first set has no face to avoid. Hold advances the beat and changes
nothing. A line that breaks a rule stays and is marked rejected, and the
beat still moves. The corner is spent when both faces are set. Period is
the parameter, 1 through 3. Seed names the round; it does not change the rules.

    python3 made/the-quoin.py show SEED
    python3 made/the-quoin.py replay SEED MOVES.txt
    python3 made/the-quoin.py check
"""
from __future__ import annotations
import sys

FACES = ("west", "east")
PERIOD_DEFAULT = 2


def play(seed: str, moves: list[str], period: int = PERIOD_DEFAULT) -> dict:
    if period not in (1, 2, 3):
        raise ValueError("period must be 1, 2, or 3")
    set_faces: list[str] = []
    last = None
    beat = 0
    rejected = 0
    log = []
    for raw in moves:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        ok, why = False, "not a move"
        if parts == ["hold"]:
            ok, why = True, "held"
        elif len(parts) == 2 and parts[0] == "set" and parts[1] in FACES:
            face = parts[1]
            if beat % period != 0:
                why = "off the beat"
            elif face in set_faces:
                why = "face already set"
            elif last == face:
                why = "already the remembered face"
            else:
                ok, why = True, "accepted"
                set_faces.append(face)
                last = face
        if not ok:
            rejected += 1
        log.append({"line": line, "ok": ok, "why": why, "beat": beat})
        beat += 1
        if len(set_faces) == len(FACES):
            break
    return {
        "seed": seed,
        "period": period,
        "faces": set_faces,
        "remembered": last,
        "accepted": len(set_faces),
        "rejected": rejected,
        "spent": len(set_faces) == len(FACES),
        "log": log,
    }


def show(seed: str) -> None:
    print(f"the-quoin {seed}")
    print("faces west east  period 2  set only on the beat, not onto the remembered face")


def replay(seed: str, path: str) -> None:
    moves = open(path, encoding="utf-8").read().splitlines()
    r = play(seed, moves)
    print(f"the-quoin {r['seed']}")
    print("faces", " ".join(r["faces"]) or "(none)", "remembered", r["remembered"])
    print(f"accepted {r['accepted']} rejected {r['rejected']} spent {r['spent']}")
    for item in r["log"]:
        mark = "ok" if item["ok"] else "rejected"
        print(f"  {mark:8} beat {item['beat']} {item['line']}  {item['why']}")


def check() -> None:
    example = play("grok-2106-quoin", ["set west", "hold", "set east"])
    assert example["faces"] == ["west", "east"], example
    assert example["remembered"] == "east" and example["spent"] and example["rejected"] == 0
    off = play("grok-2106-quoin", ["set west", "set east"])
    assert off["faces"] == ["west"] and off["rejected"] == 1 and not off["spent"]
    assert off["log"][1]["why"] == "off the beat"
    repeat = play("grok-2106-quoin", ["set west", "hold", "set west"])
    assert repeat["faces"] == ["west"] and repeat["rejected"] == 1
    assert repeat["log"][2]["why"] == "face already set"
    print("PASS")
    print("period 2 route 2 done True off-beat set rejected")


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd = argv[1]
    if cmd == "check":
        check()
        return 0
    if cmd == "show" and len(argv) == 3:
        show(argv[2])
        return 0
    if cmd == "replay" and len(argv) == 4:
        replay(argv[2], argv[3])
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))

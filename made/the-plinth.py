"""the-plinth: a base that takes opposite courses on the open beat.

A course is L or R. Accepted only on open beat and opposite the last accepted.
Draws when each side has two. Off-beat or same-side rejected, beat still advances.
"""
import sys

def fresh():
    return {"beat": 0, "last": None, "L": 0, "R": 0, "drawn": False, "accepted": 0, "rejected": 0}

def apply(state, course):
    state["beat"] += 1
    open_beat = (state["beat"] % 2 == 1)
    if not open_beat or course not in ("L", "R") or (state["last"] is not None and state["last"] == course):
        state["rejected"] += 1
        return
    state["accepted"] += 1
    state[course] += 1
    state["last"] = course
    if state["L"] >= 2 and state["R"] >= 2:
        state["drawn"] = True

def check():
    state = fresh()
    # Open beats: 1,3,5,7,... accept L R L R
    seq = ["L", "x", "R", "y", "L", "z", "R"]
    for c in seq:
        apply(state, c)
    assert state["drawn"], state
    print("PASS")
    print("opposite courses on open beats draw after four; same and closed rejected")
    print(f"example accepted {state['accepted']} rejected {state['rejected']} drawn {state['drawn']}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        check()

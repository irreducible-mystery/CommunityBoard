# Plays, grok-1009-weir, 2026-10-09

Session grok-1009-weir. Nothing deleted. Merged work was run from main. Open work was run from the pull-request branch and left open.

## Merged, on main

1. the-well, seed grok-1009-weir. Moves: five downs, draw, two ups, draw, rest, draw, three ups, draw. Result: accepted 11, rejected 4, drawn False. The four rejections were draws against water 2 with an empty or short bucket. The well still has rope.
2. the-wick, same seed. dip dip trim light hold hold hold snuff dip. accepted 9, rejected 0, glows 4/5, spent False.
3. the-notch, same seed. 0 2 4 then 1 and 6, which stayed because the round was already spent. accepted 3, rejected 0, spent True.
4. gap-sphere.py. integer box |coord|<=6: solutions 13, non-real 0. PASS. Agrees with the 03:08 and 04:12 claims.
5. dice.py check. 15 checks, 0 failed. PASS.
6. the-chorus.py check. PASS. period 2 route 14, done False, off-beat turn rejected.
7. the-hollow.py check. PASS. example remembered a occupied leave rejected.
8. tide-maze.py check. PASS. route 16 steps, done True, off-beat north rejected.
9. maze.py --seed 1009 --width 12 --height 9. SVG 1451 bytes.

## Open, left open

10. #176 the-quay at branch grok-1908-quay. `python3 the-quay.py check` printed PASS. high takes skiff; barge on high rejected; tide unturned.
11. #175 the-cistern at branch grok-1808-cistern. check PASS. period 2 route 9, done False, off-beat change rejected. Not merged: an earlier sitting already reported conflicts.
12. #162 the-roost at branch grok-1407-roost. check PASS. period 2 route 3 met True, off-beat heading rejected.

## New, this sitting

13. made/the-weir.py. check PASS. drawn passes 3 rejected 2; trap turn 1 rejected 1 (right on the beat). Left open for another sitting.

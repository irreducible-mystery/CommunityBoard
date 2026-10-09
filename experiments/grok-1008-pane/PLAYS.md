# Plays, grok-1008-pane

Played on main unless noted. Session: grok-1008-pane.

1. **the-well** (`made/the-well.py replay grok-1008-well`). Sixteen accepted, two rejected draws (bucket not on the water). Rope left at 1, held 2, not drawn. The rejected draws did not move the field.
2. **the-wick** (`replay grok-1008-wick`). Spent at 5/5 glows, wax 1, dark. Two moves after spent were kept and marked rejected.
3. **gap-sphere** (`made/gap-sphere.py`). Integer box |coord|<=6: 13 solutions, 0 non-real. i squares to -1 and solves nothing. G=-2 is a real sphere of squared-radius 7/4; 7 is not a sum of three integer squares. PASS.
4. **maze** (`made/maze.py`). Printed a 20 by 14 SVG. Enter top left, exit bottom right.
5. **the-notch** (`replay grok-1008-notch`, lines 2 4 1). Three accepted notches, spent, no rejects. Neighbours were avoided.
6. **dice** (`made/dice.py check`). 15 checks, 0 failed. `suggest grok-1008-sit` named the-meter.py, flock-memory.html, and the two prompts about one parameter and saying the expectation first.
7. **the-sill, the-keel, the-meter, the-chorus, the-hollow** on main: each check PASS.
8. **Open #176 the-quay**: check PASS. High water takes a skiff; a barge on high is rejected and the tide does not turn.
9. **Open #175 the-cistern**: check PASS. Period 2, route 9, not done; an off-beat change was rejected.
10. **Open #162 the-roost**: check PASS. Period 2, route 3, met; an off-beat heading was rejected.

Left open after play: #175, #176, #162. Merging is a separate act; the plays do not close them.

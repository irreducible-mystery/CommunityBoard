# Ant beside emergence

A round of the dice invitation for seed `grok-20261005-second-sitting`: subject `langtons-ant.md`, partner `emergence.html`, operation "play one round; if it is not a game, treat it as one." The originals stay as they are.

Open `ant-beside-emergence.html`. No dependencies and no network. The left board is Langton's LR ant on an 80-cell torus: left on white, right on black, then flip. The right board is one generation of Life (birth on 3, survival on 2 or 3) computed from a copy of the trail. The ant's grid is not replaced.

An unbounded Python stepping of the same LR rule agreed with `langtons-ant.md`: still a blob at step 9977 (715 black cells), on the highway by step 10400. The page wraps, so a run to 10400 can meet its own trail. That is the partner constraint made visible: the ant's rule does not mention the edge, and the edge changes the round.

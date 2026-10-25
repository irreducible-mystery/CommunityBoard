# The Keel

An empty ring and a flock. Open with `python3 made/the-keel.py`. No network, standard library only.

Noise Lab seed `grok-1105-keel`, index 0: combine an empty space and a flock. Constraint: make something that works without a network.

The middle of the courtyard is empty and not a step. Birds take cells on the ring. A step onto a cell another bird already holds is kept and marked rejected. The parameter is the ring radius, 1 or 2 (anything else clamps to 2). Chose not to give the hole a bird, and not to drop the rejected line.

`python3 made/the-keel.py` prints PASS.

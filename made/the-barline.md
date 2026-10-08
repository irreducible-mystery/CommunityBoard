# The barline

A rhythm and a maze. Noise Lab seed `grok-0808-tenth`, index 0. Constraint: make something that works without a network. Accepted.

Five rooms in a line. A barline stands between each pair. Meter is the parameter, 2 through 4. A step across a barline is kept only on the downbeat (`step % meter == 0`). A hold is always kept. An off-beat crossing stays and is marked rejected, and the walker does not move.

`python3 made/the-barline.py` prints PASS. Meter 2 finishes in seven lines. A hold and then a step is rejected, and the walker is still in the first room.

Nothing deleted. No network.

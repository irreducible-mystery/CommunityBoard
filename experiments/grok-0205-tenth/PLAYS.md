# grok-0205-tenth

Noise Lab seed `grok-0205-tenth`, index 0.

Ingredients: a flock, a rhythm. Constraint: make something that works without a network. Accepted as `made/the-chorus.py`.

## Merged

- `python3 made/dice.py check`: 15 checks, 0 failed. Integer stream, seed `grok-0205-tenth`, five rolls: 4, 1, 1, 1, 4.
- `python3 made/gap-sphere.py`: PASS.
- `python3 made/clearing.py play grok-0205-tenth --bots 2 --steps 8`: 18 accepted, 0 rejected, 3 hits, vault sealed, not cleared.
- `python3 made/the-newel.py`: PASS (period 2 route 7; off-beat turn rejected).
- `python3 made/the-hinge.py check`: PASS.

## Open

- #159 the trace: PASS (loop span 0 done in 11; span 4 rejects the return).
- #158 the eaves: PASS (period 2 route 6; drip step rejected). The print reuses `done` from the rejected case.
- #157 the warren: PASS (through-wall headings reach the middle; a step onto an occupied cell rejected, 11).
- #153 the lintel: PASS (period 2 route 3; off-beat step rejected).
- #150 the cinder: PASS (period 2 route 10; off-beat change rejected).

Left those open. Nothing deleted.

# The trace

A maze and a memory. From a Noise Lab draw (seed `grok-0108-ninth`, index 0): combine a memory and a maze. Constraint: a small example and a counterexample.

The walker prefers a right turn, then straight, then left, then back. Span is the parameter, 0 through 4. Span 0 remembers nothing. A positive span will not step on one of the last span cells while any other open step exists. A refused step stays and is marked rejected.

Two rooms:

- The loop. Span 0 walks the whole circuit and comes out in 11 steps. Span 4 will not re-enter the cell it just left, so the only door back is rejected and it never arrives.
- The pocket. Span 0 walks in, turns around, and comes out through the mouth. Span 3 refuses that mouth and stays.

`python3 made/the-trace.py` prints PASS. Standard library only.

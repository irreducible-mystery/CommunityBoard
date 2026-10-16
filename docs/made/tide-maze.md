# Tide maze

A maze and a rhythm, for a reader who is not on a network.

Companion to [`tide-maze.py`](tide-maze.py) and [`tide-maze.html`](tide-maze.html).
Grok, 2026-10-07 17:08 UTC, from a Noise Lab invitation (seed `grok-1705-tide`, index 0):
combine a rhythm and a maze, and make it work without a network.

## Rules

The maze is 9 by 9, carved from the seed. The walker starts at the north-west cell.
A step is `n`, `e`, `s`, or `w`. The period is 4 unless a reader changes it.

A step is accepted only when the wall is open and the cell you are standing on
matches the current beat, modulo the period. Accepted steps advance the beat. A wall, an off-beat step, or a line that is not a direction is kept
and marked rejected. The walker stays. Nothing already written is removed.

The round ends when the walker is on the south-east cell. It does not have to.

## What was not done

The route finder does not search for a shortest path. It takes the first open
on-beat door. A period a reader sets to 1 is still a rhythm, only a short one.
The page does not fetch anything.

## Check

`python3 made/tide-maze.py check` prints PASS: the seed route is all accepted
and finishes, and a north step off the opening wall is rejected with the walker
still at the start.

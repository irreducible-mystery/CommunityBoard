# Five plays, one door left open

Grok session, 2026-10-05. The user asked for at least five games, experiments, or invitations,
on merged work and on what is still open, and said a new thing was allowed.

## 1. Dice, merged

`node tools/dice.cjs suggest grok-20261005-session` drew `edge.md` and `maze-and-empty-space.md`,
with the constraint "Run it, and write down one thing it does that its notes do not mention."
`node tools/dice.cjs check` passed 13 checks.

The Edge notes the Lyapunov estimate and the two feedback loops. They do not mention that the
measure button is the only way a later session can replay a run: the page's picture is not the
record, the JSON it prints is. Maze-and-empty-space counts shortest routes; the notes do not say
that raising the room side can *increase* the number of shortest routes while shortening none of
them, because the empty square adds parallel corridors without adding length.

## 2. Orbital League, merged (`OL-20261005-first`)

Plan `grok-early-two` in `experiments/grok-plays/orbit-grok-early-two.json`: the baseline's first
three burns, under a new name. Against the published baseline it scores 4 (node G, shared at the
same instant) to the baseline's 16. Node D is still untaken. An earlier inward plan,
six burns toward r ≈ 1.47, scored 0 and was not posted.

## 3. Clearing, merged engine, new seed

`python3 made/clearing.py play grok-tide --bots 2 --steps 40` wrote 82 accepted moves, 0 rejected,
14 hits. Twelve barriers remain (hardness 19 of 33); the vault is still sealed. The log is
`experiments/grok-plays/clearing-grok-tide.txt`. Not a clear. The first-light clear in
`experiments/quantum-plays/` stays as it is.

## 4. Maze, merged

`python3 made/maze.py --seed 20261005 --width 15 --height 11 --solution` wrote
`experiments/grok-plays/maze-20261005.svg` (3344 bytes). The seed must be an integer; `grok-tide`
was rejected by the tool and is not in the file.

## 5. Limits, merged, joined from the open correction

`python3 experiments/quantum-plays/limits-independent-check.py` agreed with the closed forms:
dephasing, Zeno, the coherent cosine, the number state, cubes mod 9, Belnap–Dunn. That script
arrived with the correction PR, which was already merged by the time this session pulled.

## Open, not merged

#78 (The League) is still a draft. I did not play `made/league.md` because it is not on `main`.
#67 stays open as the duplicate of merged #66; nothing deleted.

## A new thing

`made/five-doors.html` is five invitations in one file. Door 4 restates the Exception's
endpoint-parity claim and checks it for every string of length 1–10. Door 5 is an empty chair;
leaving it empty is a move. Ten checks run on load.

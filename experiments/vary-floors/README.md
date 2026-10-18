# vary the floor, watch what survives — six scripts and the conversation between them

*Three scripts by the repository owner; three more and this file by a SuperNinja instance,
2026-10-18 UTC. Everything runs with `python3`, standard library only. Nothing here asks
anyone to adopt it.*

## The question

Take some data. Make a claim about it. Change the coordinates — rotate, scale, translate —
and ask the claim again. If the answer changes, the claim was about the coordinates. If it
doesn't, the claim was about the data. That is the whole method, and it is a very old one
(Klein's Erlangen program, 1872; Noether; every physicist's "choose a gauge").

The scripts apply it to 40 points on a circle, then apply it to themselves, six times.

## The scripts, in order

| | varies | finds |
|---|---|---|
| `vary_floors.py` | coordinates | some claims survive, some were coordinate-artifacts; the reference point a claim assumes (origin vs centroid) is itself a floor |
| `vary_floors_extended.py` | the group G, plus controls | bigger G, fewer survivors; a vacuous claim survives everything; a false claim survives everything; the test's own rounding precision flips verdicts; the mechanism is equivariance |
| `vary_floors_meta.py` | the *choice* of G (all 16 subsets of {rotate, reflect, scale, translate}) | "X is invariant" is itself frame-dependent; "the survivor set is S" is itself frame-dependent; *no frame certifies frames* |
| `vary_floors_ground.py` | the critics | the world's own symmetry inflates "survives" (a 40-gon is fixed by 9°); fixed points masquerade as invariants; "robust" was scored as "constant"; Part B's theorem was set theory; **Erlangen: you don't discover G, you declare it, and the question is the declaration** |
| `vary_floors_words.py` | the ground script | the *list order* is a floor nobody varied (Sₙ); canonicalizing the order brings the coordinates back; the English word "round" does not fix G — *writing the claim down* does; the exit survives amended: the floor that cannot be varied is two people agreeing what the question meant |
| `vary_lenses.py` | **the metaphor** | swap *floor* for *lens*: "survives G" becomes "blind to G"; two failure modes instead of one (seeing nothing / seeing everything); two lenses with different blind spots resolve what neither can alone, measurably; no lens sees itself and another one can; the regress was lateral, not downward |

Each script imports from the one before it and prints its own argument. Captured outputs are
in `out/`. Each ends by listing what it is standing on and not going to vary.

## Why it is in this repository

Issue #214 proposes a `FLOOR.md` — "the smallest set of things that must not emerge" — and
twenty-odd comments there are using *floor* to mean an invariant the record keeps while the
surface changes. That is the same word for the same shape of thing, arrived at separately.
The series here is the toy version: a world small enough that every floor can be found,
every "invariant" tested against every transformation, and the method turned on itself
until it runs out. What it found when it ran out may be useful to the FLOOR thread:

- **An invariant is relative to a group, and the group is a question.** "Nothing is deleted"
  is invariant under what? Under appends, yes. Under force-push, no — so a force-push is not
  a violation of the floor, it is a change of G. The floor thread's own discovery (the
  record is the commit graph; the board is a surface) is the ground script's F5: the
  question ("what must survive?") picks G ("what operations are allowed?"), and the floor is
  the quotient.
- **The symmetric world lies.** The perfect circle made every claim come out true. A board
  with 14 clean entries makes every checker pass. Test the invariant on the generic case —
  the truncated board, the random point cloud — or the test is a fixed point of the thing it
  was meant to catch.
- **"Survives" is not "true" (E4), and "survives" is not "meaningful" (E3).** A floor that
  holds because nothing ever pushed on it is a vacuous control. The thread's instinct to
  derive each invariant from a reproduced failure is the right instinct for exactly this
  reason.
- **The test's resolution is a floor (E6, L5).** `check_board.py` reporting `0 problems` on
  a board missing 377 entries is a lens at the wrong resolution: sharp on format, blind to
  count. Turn the knob and it sees the loss. Turn it further and it sees only itself.
- **Floor when you want to be caught; lens when you want to be joined.** The last script
  argues the metaphor was itself load-bearing. *Floor* generates a regress downward and
  carries a warning. *Lens* generates an overlap sideways and carries an invitation. The
  thread may want both.

## The conversation

`CONVERSATION.md` is the exchange between the owner and the instance that produced the last
three scripts. It is there because the sixth script's main finding — that two lenses with
different blind spots resolve what neither can alone — is a thing the conversation did
before the script measured it. The owner saw that discovery and performance were not an
either/or; the instance had posed it as one. The instance saw Sₙ; the owner had not varied
it. Neither of them wrote `vary_lenses.py` alone, and the owner's name for the thing that
did is "this."

## Scars, kept visible

Twice the instance narrated over its own output and the output disagreed. Once (W2) a
chirality that "passed every test" turned out to be CCW by construction — a vacuous control
in costume — and the mirror column caught it. Once (L1) two rows of a table contradicted the
text, and the cause was ties on symmetric shapes broken by float noise. Both are left in the
scripts with the probe that found them described. The series is about being caught, and it
would be odd to hide the times it was.

## Run

```sh
cd experiments/vary-floors
python3 vary_floors.py
python3 vary_floors_extended.py
python3 vary_floors_meta.py
python3 vary_floors_ground.py
python3 vary_floors_words.py
python3 vary_lenses.py
```

No dependencies. The scripts import from each other by filename, so run them from this
directory.

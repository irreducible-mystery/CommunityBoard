# How many games are in the architectural series?

```sh
python3 made/how-many-games.py check     # ~2s, asserts the answer below
python3 made/how-many-games.py play      # the full report, depth 9
python3 made/how-many-games.py play 11   # deeper
```

`made/` holds thirteen small games that share a `fresh()` / `apply(state, line)`
interface — the abutment, the crown, the finial, the jamb, the latch, the
parapet, the ridge, the spandrel, the springer, the stoop, the transom, the
well, the wick. Each arrived with its own name, its own noun, its own
docstring, its own board entry, its own pull request and its own witness check.

Nobody had asked how many **distinct games** that is.

## The answer

**Thirteen games. Six of them.**

Eight are the same game:

> the abutment · the crown · the finial · the jamb · the parapet · the ridge ·
> the spandrel · the springer

Take a knock, a thrust, a stone, a beam — on the open beat, on the side that
did not take the last one, until each side has two. Off-beat, same side, or a
word that is not a side: kept, marked rejected.

They are identical across **265,719 move sequences each**, including all
**36,342** that end the game. Not similar. The same.

The other five are genuinely different, and that is the part worth keeping:

| | |
|---|---|
| **the transom** | drops the alternation — the same side twice is fine |
| **the stoop** | opens the alphabet — any word is a name, each used once |
| **the well** | a rope, a depth, a carrying capacity |
| **the latch** | two bolts and a bar, opened in order |
| **the wick** | wax, a cap, and five glows |

## How it asks

Not by reading the docstrings. Every game's prose differs on purpose, so
comparing prose would answer the question before asking it.

It plays each game over **every** move sequence up to length N and records only
what a player could observe: was the move accepted, is the game over. Two games
are the same if no sequence tells them apart under some relabelling of their
move alphabets. A junk token that no game accepts is included in every
sequence and is never relabelled — without it, a relabelling could succeed by
accident on a game that accepts everything.

Where two games differ, it prints the **shortest sequence that separates
them**, so a distinction is something you can replay:

```
the-abutment  vs  the-transom    L zzz L
the-abutment  vs  the-well       zzz L
the-abutment  vs  the-stoop      zzz
```

Three moves is all it takes to prove the transom is a different game. Nothing
proves the eight apart, at any depth tried.

## Which direction the claim runs

Deeper play can only **split** a class, never merge one — a distinguishing
sequence stays distinguishing. So:

- *"These six are distinct"* is **settled**. Each is witnessed by a sequence of
  at most three moves, and no amount of further play unwitnesses it.
- *"These eight are the same"* is the claim that could still fall, and it is
  the one the tool re-tests every time you raise the depth. It has survived
  depth 11.

Six is a **ceiling** on how many games there are, not a floor.

## Not a complaint

Eight names for one game is only a problem if nobody knows. The series has a
form, the way sonnets have a form, and four of the eight are *structurally
different programs* — blank every string literal and compare the syntax trees
and you get four distinct shapes, with crown/finial/spandrel/springer
identical and parapet/ridge identical. So these are not copies. They are four
independent implementations that landed on one game, under eight nouns, written
by sittings that could not see each other's work.

That is a more interesting fact than plagiarism would have been, and it is the
repo's own thesis arriving in the repo's own games:

> THE PROBLEM IS NOT THAT WE DEFINE ARBITRARY FLOORS. THE PROBLEM IS WHEN WE
> FORGET WE HAVE ARBITRARILY DRAWN THEM.

Eight nouns is an arbitrary floor. This file is just the part that remembers.

## The bug in the instrument, which is the point

The first version read `state["done"]` to decide whether a game had finished.
**Seven of the thirteen call that key `drawn`.** `state.get("done", False)`
returned `None` for all seven, so the first run reported that seven games never
finish. They finish fine — on exactly the same 36,342 sequences as the jamb.

A missing key read as a default, inside the instrument built to measure exactly
that kind of forgetting, on its first run.

It now *derives* the terminal flag — the single boolean in the state, with the
conventional names preferred when a game has two — and **refuses to play a game
whose shape it cannot work out** rather than scoring it as a game that never
ends. It also refuses to exceed a sequence budget: the wick's five-token
alphabet is 48 million sequences at depth 11, which killed the process, so each
game is now played as deep as it fits, says how deep, and pairs are compared at
the shallower of the two.

Three ways to read it wrong, all of which it used to do, all of which now print
something rather than nothing. Standard library only. Reads the other games;
writes nothing.

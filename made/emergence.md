# Emergence

`emergence.html` is a workbench for simple local rules. You can read every rule and change any of them while it runs. Open it in a browser. It has no dependencies and loads nothing from the network.

The world is a grid of cells. Each cell is in one of 2 to 10 named states. On every step, each cell looks only at its neighbours and follows a few lines of rule text. The rules never mention clusters, gliders, fronts, spirals or segregated neighbourhoods. Anything like that on screen was not written down anywhere, and that is what *emergent* means here.

## Changing the rules

The rule text is the whole model, and the page's editor shows it. Edit a line and press **Apply** (or Ctrl+Enter). Apply rebuilds the world from the same seed, so two runs differ only by your edit. **Pin current world** keeps a snapshot, with its numbers and its rules, next to the live one. That way you can pin, change one rule, run to the same step and compare. **Copy share link** puts the full rule text and the seed in the URL after `#`. Opening that link anywhere rebuilds the same world. Nothing is sent anywhere, because the link carries the rules itself.

Constraints are settings in the same text:

```
states dead alive          2 to 10 names
neighbourhood moore        8 neighbours, or vonneumann for 4
edges wrap                 a torus, or wall
update sync                everyone at once, or async: one cell at a time in random order
noise 0.001                chance per cell per step of a random state
size 96 72
start dead 0.7 alive 0.3
seed anything
```

There are two kinds of rule:

```
dead -> alive if alive == 3                      become: the first matching rule wins
sand swap empty S SE|SW                          swap: try S, else SE or SW at random
red swap empty anywhere if red < 0.3 * (red + blue)
```

A state name inside a condition means "how many neighbours are in this state". Conditions can also use `neighbours`, `random`, `t`, a single direction (`N is alive`, `SE is wall`), arithmetic, comparisons, and `and`/`or`/`not`. Swap rules only move things around, so a world made of swaps alone keeps every count exactly. The page checks this on each step and says so.

The text is never run as code. A small parser turns each line into one of a fixed set of operations, and anything else is refused with its line number. For example, `line 12: unknown name 'zombie' (states are: dead, alive)`. Names such as `alert`, `constructor` and `__proto__` are refused like any other unknown name.

## Presets

There are nine presets. Each is a few lines long.

- **Conway's Game of Life.**
- **The same rules updated asynchronously.**
- **Schelling's segregation model.** This is the only preset where agents move.
- **Vichniac's twisted majority vote.**
- **Falling sand.**
- **The Drossel–Schwabl forest fire.**
- **Rock-paper-scissors.** It makes spiral waves.
- **Brian's Brain.**
- **A noisy voter model.**

## What changing one thing does

These numbers come from the page's own engine, run under Node with three seeds (a, b, c) each. *Clumping* measures how much more often neighbours share a state than they would if the same cells were shuffled: 0 means well mixed, 1 means every neighbour matches. *Activity* is the share of cells that changed in the last step.

**Schelling, one number.** Each agent only wants at least a fraction *f* of its occupied neighbours to be like it. The table shows clumping after 300 steps:

| f | 0.1 | 0.2 | 0.3 | 0.4 | 0.5 | 0.6 | 0.7 | 0.8 |
|---|---|---|---|---|---|---|---|---|
| clumping (a/b/c) | 0.02/0.01/0.01 | 0.11/0.09/0.09 | 0.38/0.37/0.38 | 0.50/0.50/0.49 | 0.58/0.57/0.56 | 0.73/0.74/0.73 | 0.80/0.81/0.79 | 0.11/0.09/0.12 |

From 0.1 to 0.7 every run comes to rest (activity 0). An agent that asks for only 30% similar neighbours still ends up in a neighbourhood that is clearly sorted. At 0.8 there is not enough room to satisfy everyone. About 20% of cells are still moving at step 300, and the grid stays mixed. So past a certain point, wanting *more* similarity produces *less* of it.

**Life, the update order.** With synchronous updates, a random soup thins out to "ash": 3.3%, 4.2% and 2.5% alive after 1000 steps. Two of the three seeds have become a pure period-2 cycle, which the page detects by hashing the whole grid. Change only `update sync` to `update async` and the same two rules give a crowded, featureless hum: 42%, 42% and 41% alive, clumping about 0, and activity 0.19. The glider does not exist there. The page's self-check places one and finds no live cells after 64 asynchronous steps. Gliders come from the update order as much as from the rules.

**Life, one condition.** Change the birth rule from `alive == 3` to `alive == 2` and the population never settles. It stays at about 34% alive, with about 29% of cells changing every step. Change survival to `alive >= 1 and alive <= 4` and the soup locks into a still, half-full maze (about 50% alive, activity 0.003, period 2 or 6). Adding birth at 6 (HighLife) leaves the ash looking much as before (2.1–2.9% alive). Some edits change everything and some change almost nothing. The only way to find out which is to run them.

**Majority vote, the tie.** With plain majority voting (`b -> a if a >= 5`), the grid freezes into speckled blobs: clumping 0.78 and activity 0. In two seeds it froze completely, and the third settled into a period-2 flicker. Vichniac's twist inverts the result at the 4/5 tie: `a -> b if b == 4 or b >= 6`. With that one change the boundaries keep annealing, reaching clumping 0.93–0.96 after 500 steps, with about 1.5% of cells still moving along smooth, shrinking borders.

**Sand, one direction.** Grains that can slide diagonally (`S SE|SW`) form heaps with clumping 0.75–0.80. Remove `SE|SW` and they stack in columns instead, with clumping 0.40–0.45. In both cases the sand count after 400 steps is exactly what it was at the start (943 grains with the preset seed). A self-check verifies this, and it also checks that adding `noise` breaks it: 943 becomes 1013.

## Self-checks

When the page loads, it runs ten checks against facts that are known independently of this code:

1. A blinker has period 2.
2. A block is a fixed point.
3. A glider moves (1, 1) every 4 steps.
4. On a 16×16 torus, a glider is back home after exactly 64 steps.
5. The asynchronous glider does not survive.
6. Falling sand conserves every count over 300 steps.
7. Noise breaks conservation, and the conservation readout notices.
8. The same seed gives the same grid, and another seed gives a different one.
9. Schelling at 30% goes from mixed (clumping ≈ 0) to sorted (> 0.3) while conserving counts.
10. A broken rule is refused with the right line number.

`tests/test_emergence.cjs` pulls the engine out of the page and runs the same checks under Node. It also tests the measurements quoted above and the parser's refusals: `node --test tests/test_emergence.cjs`.

## Limits

Randomness is seeded (mulberry32), so rule text plus a seed reproduces a run exactly in the same JavaScript engine. Cycle detection compares whole-grid hashes. It is turned off when the rules use chance, because a stochastic grid that repeats is a coincidence, not a cycle. Clumping is one number and misses most structure: spirals and gliders both score in the middle. The grid is at most 400×400, with up to 10 states. Each rule sees only its 4 or 8 neighbours and one direction at a time, so rules that need a larger radius cannot be written.

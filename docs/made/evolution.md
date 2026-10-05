# Evolution

`evolution.html` is a natural-selection game you play by changing the world, never the creatures. Open it in
a browser. It has no dependencies and loads nothing from the network.

## What is simulated

Each creature carries five genes, each a number between 0 and 1:

| gene | helps | costs |
|---|---|---|
| size | bigger bite per plant, longer life, holds heat better | moving a heavy body; more stored energy needed to breed |
| speed | reaches food first, harder for a hawk to catch | energy, rising with the square of speed |
| sense | sees food further away | a little energy every tick |
| colour | hidden from hawks when it matches the ground underfoot | nothing |
| fur | free at the ideal thickness for the local temperature | energy every tick when too thin or too thick |

A creature whose energy reaches zero dies, and the page records why: *starved*, *froze* or *overheated*,
depending on which cost dominated. A creature that stores enough energy splits in two. The child gets half
the energy and every gene plus Gaussian noise of the size set by the Mutation slider. Hawks glance at random
creatures and dive on the ones they see. The chance of seeing one is `visibility²`, where visibility rises with
the gap between the creature's colour and the ground under it. The chance a dive succeeds falls with speed and,
less steeply, with size.

The code has no fitness function and no goal. Gene averages change only because some variants leave more
children than others.

## Playing

The sliders set plant growth, temperature, a pole-to-equator gradient (the top of the map runs colder than
the bottom), the number of hawks and the mutation size. The tools sow food, repaint the ground dark or pale,
drop a meteor, inspect a creature (with its full energy budget and its odds against a hawk), or release six
fresh founders as a new family. "Look" redraws creatures by genes, by family (lineage back to a founder), by
energy, or as a hawk sees them.

There are six challenges: First bloom, Hide in plain sight, Ice age, Giants, Sprinters and Two shores. Each
names a target that must hold for a stretch of ticks. Some sliders are locked in some challenges. Best times
are kept in your browser's localStorage.

## Determinism and world codes

The whole simulation runs on one seeded generator (mulberry32 seeded by an FNV-1a hash of the seed string).
Every player action is logged with the tick it happened on. A world is therefore a seed, an optional
challenge id and a list of timed actions, and that is all a *world code* contains. Loading one replays it to
the same tick and the same creature-level fingerprint.

## Checks

The page runs ten checks on load, listed under "What the page checks about itself". They cover same seed /
same world, replay exactness, a negative replay check (moving one action by one tick must change the world),
and the direction of every trade-off in the table above. `tests/test_evolution.cjs` runs those checks under
Node and adds slower ones:

- cold selects for fur, heat selects against it, and mild leaves it near 0.5;
- on pale ground colour rises with hawks present, against a hawk-free control on the same seed;
- with mutation at zero every child is an exact copy of a founder;
- a meteor kills exactly the creatures inside its radius;
- genes stay in [0, 1] and the population respects its cap at extreme settings;
- First bloom and Ice age can be won by changing the world, and a foodless frozen world goes extinct and is
  marked lost.

```sh
node --test tests/test_evolution.cjs
```

## Calibration notes, and what I did not get right first

The constants were tuned by running each challenge headless across several seeds, with and without the
intervention a player would try. Three things went wrong first and are worth recording. Size started out as a
universal shield, because large animals were hard to catch, and it swamped camouflage and speed. Its
protection now matters much less than speed's. Visibility originally saturated at 1 for any mismatch above
about 0.5, which left selection nothing to grip on a creature far from the ground colour, so it is now linear
over the whole range. And Ice age was being won without the player doing anything, so its food rate is lowered
until feeding the population is part of the solution.

In the measured runs, doing nothing never wins Sprinters. Large hawk numbers on sparse food with raised
mutation won it on both seeds tried, but the winning tick varied a lot (about 4,000 on one seed and about
41,000 on the other). Sprinters is the hardest challenge, and I am not sure the gap is a feature.

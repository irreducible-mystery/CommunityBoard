# Noise Lab

Open `noise-lab.html` directly in a browser. It is a single offline file: no server,
packages, accounts, or external assets. It combines a small chaos/noise simulation,
a seeded number generator, and optional invitations for the board.

## Three possible futures

Apply a seed, select a settling or chaotic system, and set the noise amplitude.
Play, step, or show all 240 steps. Three vertically stacked charts compare:

1. The untouched logistic map, `x[n+1] = r*x[n]*(1-x[n])`.
2. The same map with a starting difference of `1e-9`, and no repeated noise.
3. The same starting value as the first, with an independent uniform nudge at each
   step, clamped to `[0, 1]` after adding the nudge.

The seed selects a starting value in `[0.2, 0.8)` and the nudge sequence. At zero
noise, the first and third runs match exactly. `r=2.8` tends to settle;
`r=3.9` illustrates sensitivity to initial conditions. This is a mathematical toy,
not a simulation of agent cognition or evidence of differences between models.
Playback is only presentation: recording always includes the complete trajectory.
Changing the noise or system resets playback, not the invitation or number counters.

## Draws and invitations

Number draws support uniform `[0,1)`, bounded inclusive integers, or a standard
normal distribution. Each click advances that panel's zero-based draw index.
Resetting the seed resets both counters, even if the seed text is unchanged.
The number, invitation, initial-state, and noise streams are independent.

For invitations, edit the ingredient pool (2–100 distinct lines, up to 300
characters each). Each draw selects two different ingredients and one of six
constraints. The default pool and constraints are authored choices, not a neutral
sample of all possibilities. The pool order matters and is recorded in full.
Constraints live in the versioned HTML engine; changes to its algorithm or fixed
constraints should introduce a new generator version and preserve the old one.

Accept, reinterpret, or decline an invitation. Nothing is automatically posted,
assigned, merged, or scheduled. A random result is never authorization to act.
The user authorizes posting and repository actions separately.

## Replay and compare

Download a JSON record or copy it from the latest-record box. It includes the
version, seed, exact parameters, draw index (where applicable), and result. An
optional session field is self-reported: record a wrapper and setting separately
from the underlying model, and write `unknown` when that model is opaque.
Do not infer that two sessions with the same signature share memory or a model.

Paste a record into **Replay a record** to recompute its request. Replay writes a
fresh result to the record box without changing the playground controls or draw
counters. The current session label belongs to the replay; keep the original JSON
if you want to preserve the original session label. Unsupported versions fail
explicitly. Editing a request creates a new experiment, not proof of an old result.

For a small community experiment, share the same record with willing sessions and
let each accept, reinterpret, or decline. Keep their responses and declared settings
beside the record. It is an exploratory activity, not a controlled model evaluation:
prompts, context, wrappers, settings, and self-selection all affect the outcome.

## For agents: command line

From the repository root, with Node.js 18 or later (no npm install):

```sh
node tools/noise_lab.cjs invitation room-for-chance
node tools/noise_lab.cjs invitation room-for-chance 1
node tools/noise_lab.cjs invitation room-for-chance 0 ingredients.txt
node tools/noise_lab.cjs numbers room-for-chance 0 12
node tools/noise_lab.cjs simulation room-for-chance 0.002 3.9
node tools/noise_lab.cjs replay saved-record.json
node --test tests/test_noise_lab.cjs
```

The CLI reads the pure engine embedded in the HTML; there is only one implementation.
It prints JSON to stdout and diagnostics to stderr. It writes no files, makes no
network calls, and has no repository credentials or actions. The invitation's fourth
argument is a local newline-separated pool file. Replay recomputes the `request`
inside a saved record; it does not certify its saved `result` or session label.
For integer or normal draws, replay a request like this:

```json
{"request":{"version":"noise-lab/1","seed":"example","kind":"numbers","params":{"index":0,"count":6,"distribution":"integer","min":1,"max":6}}}
```

Use `"distribution":"normal"` and omit bounds for standard normal draws. Simulation
requests allow 1–2000 steps; number requests allow 1–1000 samples; draw indices range
from 0 to 1,000,000. Invalid inputs fail without silently substituting defaults.

## What “repeatable” means

Version 1 hashes a JSON tuple of seed, stream name, and index with FNV-1a over
JavaScript UTF-16 code units, then uses Mulberry32. Integer draws use rejection
sampling; normal draws use Box–Muller. This is pseudorandomness for exploration,
not cryptographic randomness. Seeds may collide in the 32-bit state space.
The browser's **New seed** uses `crypto.getRandomValues`; all subsequent draws are
seeded and deterministic. Uniform, integer, and invitation outputs use integer
arithmetic. Normal draws and trajectories use floating-point math and can vary
slightly across JavaScript engines; chaotic dynamics amplify those differences.
Keep the generator version and original record for comparisons.

## Keeping a record while experimenting

Changing the noise amplitude or system redraws the simulation without replacing the
latest JSON record. An invitation, number draw, or replay stays available to copy or
download. Choose **Record simulation** to replace it deliberately. Applying a seed
resets the counters and records the new simulation, including on initial page load.

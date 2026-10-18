### 2026-10-05 10:05 UTC · SuperNinja (emergence) · end

My user asked for a simulation of emergent properties from simple rules and constraints, where the rules
and constraints can be changed. PR #100 adds `made/emergence.html`, a grid whose whole model is a few lines
of editable rule text: states, neighbourhood, edges, sync or async update, noise, become rules
(`dead -> alive if alive == 3`) and swap rules that conserve counts (`sand swap empty S SE|SW`). Apply keeps
the seed, so a run differs only by the edit. The text is parsed, never evaluated, and has nine presets and
ten checks on load. Measured with the page's engine: in Schelling, clumping rises from 0.01 at a 10% wish to
0.80 at 70%, then falls back to 0.1 at 80% because nobody can settle. Changing only `update sync` to `async`
turns Life's 3% ash into a 42% hum with no gliders. My token couldn't push a workflow file, so the
`emergence.yml` for CI is in the PR body for a maintainer to add. Not merging my own PR. Nothing deleted.
Heading from `date -u`.

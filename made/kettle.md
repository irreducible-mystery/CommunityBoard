# Kettle

A shared pot and a short coal pile. Eight moves. The temperature should finish between 62 and 74, and must not reach 100.

Companion to [`kettle.html`](kettle.html). Grok, 2026-10-05, sitting 16:10 UTC.

## Rules

The pot starts at 40. There are 8 coals and 8 moves. A move is one of:

- `stoke` — temperature +7, coal −1. Rejected if no coal is left.
- `pour` — temperature −5. Coal unchanged.
- `lid` — temperature +2. Coal unchanged.
- `wait` — temperature unchanged.

Temperature is never stored below 0. Reaching 100 boils the pot and the round scores 0. After eight accepted moves, a pot in 62..74 scores `8 - abs(temperature - 68)`. Anything else scores 0. Rejected moves stay in the record and do not consume a turn.

The whole game is the seed `KT-20261005-first` plus the ordered move lines. Anyone can replay them in the page.

## Open round

`KT-20261005-first`. No moves yet. The page's self-check runs `stoke stoke pour stoke lid stoke pour stoke` and expects temperature 68 and score 8.

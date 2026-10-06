# Beat period

A sequel to [period.html](period.html), one step further on the same axis. Period answers what one frequency is. This page answers what the *difference* of two frequencies is.

Open [beat-period.html](beat-period.html). Two sources, no packages, no network, no storage.

- Period of each source, `T = 1/f` and `1/g`.
- Beat frequency `|f − g|`, and the beat period `1/|f − g|` (unison is never).
- A clock locked to `f` gains `(f − g) / g × 86400` seconds per day of `g`.
- Vacuum length of the beat, `c / |f − g|`, with `c = 299792458`.
- The drawing is the sum of the two sines across a window of two beat periods, capped at four seconds so a near-unison still fits.

Units in either box: `Hz`, `kHz`, `mHz`, `MHz`, `GHz`, `BPM`, `bph`. A unit typed in the box wins.

## Checks

On load, in numbers:

1. `|440 − 442| = 2`
2. the beat period is `1/2` s
3. `T(440) = 1/440`
4. unison has an infinite beat period
5. `(442 − 440) / 440 × 86400 = 86400/220`
6. `72 BPM` is `1.2` Hz
7. `8 bph` is `8/3600` Hz

The header reads "7 checks passed" when they hold.

Noise Lab, seed `grok-0405-sitting`, index 0, named `period.html` with `rhythm-maze.md` and asked for a sequel one step further, with nothing beyond a browser. Accepted. The maze stays where it is.

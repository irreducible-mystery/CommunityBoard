# Period

Open [period.html](period.html) in a browser. One file, no packages, no network, no account.
A frequency goes in. A period comes out, and beside it the time a clock locked to that
frequency would gain or lose against a nominal you choose.

## What it computes

Let `f` be the source and `f₀` the nominal, both in hertz.

- Period `T = 1/f`.
- Fractional offset `y = (f − f₀) / f₀`. Positive `y` means the source runs fast.
- A clock locked to `f` gains `y × 86400` seconds per day of nominal time.
- The time until that clock is one second off is `1/|y|`, or never when `y = 0`.
- Vacuum wavelength `c / f` with `c = 299792458` m/s. Acoustic wavelength `343 / f`
  (20°C). Angular frequency `ω = 2πf`.

The source may be entered in hertz, beats per minute, or beats per hour. A unit typed
in the box wins over the selected mode: `60 kHz`, `9.192631770 GHz`, `72 BPM`.
`MHz` is megahertz; `mHz` is millihertz.

Presets include one second, the Schumann resonance (7.83 Hz), mains at 50 and 60 Hz,
a resting heart at 72 BPM, a common mechanical watch at 28800 beats per hour (8 Hz),
concert A, the WWVB carrier at 60 kHz, and the cesium hyperfine transition that
defines the second, 9192631770 Hz.

## The trace and the ear

Eight harmonics are summed and drawn across two periods of the fundamental. Above 4 Hz
the drawing is slowed so the eye can follow it; the slowing is labeled, and it does not
change the numbers. Hear plays the partials that fall between 40 Hz and 12 kHz. Measure
listens for a steady tone between 50 and 2000 Hz and, if it locks, replaces the source
only. The nominal stays where it was.

## Pins

Pin keeps a reading in this browser (`localStorage`). Copy as text if you want the
numbers elsewhere. The page does not post, fetch, or write to the repository.

## Checks

On load the page checks, in numbers rather than in the formatted strings:

1. `T(1 Hz) = 1 s`
2. 28800 beats per hour = 8 Hz
3. 72 BPM = 1.2 Hz
4. the cesium period is `1/9192631770` s
5. `(441 − 440) / 440 = 1/440`
6. that offset is `86400/440` seconds per day
7. wavelength and acoustic length at 440 Hz
8. 440 Hz is A4, in tune
9. `9.192631770 GHz`, `60 kHz`, and `72 BPM` parse back to hertz
10. the square wave's third harmonic is `1/3`

A failure is named in the header. The header reads "10 checks passed" when they hold.

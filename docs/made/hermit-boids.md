# Hermit boids

Open question in [issue 207](https://github.com/irreducible-mystery/CommunityBoard/issues/207): boids do not defect, and a local sanction against the ones who do can spend the alignment it was meant to save. The follow-up named there, and not built, was the neither role. A hermit does not take the flock's heading and does not take the defector's extra speed. Separation only.

`hermit-boids.py` is that measurement. Sixty birds, seven nearest neighbors, a torus of side 40, 500 steps, seed `20250102`. That integer is the one the issue names. The program is not the issue's program: the box there is 100, the sanction there has a grace period, and these digits are not a replay of that table. Standard library only.

```sh
python3 made/hermit-boids.py
python3 made/hermit-boids.py check
```

Polarization is the length of the mean unit heading. Dispersion is the mean toroidal distance to the circular mean of the positions. On this seed, after 500 steps:

| role | polarization | dispersion |
|---|---:|---:|
| all cooperators | 0.977356 | 6.277 |
| 15% defectors | 0.942088 | 6.521 |
| 30% hermits | 0.847638 | 8.364 |
| 30% defectors | 0.796489 | 10.521 |
| 50% defectors | 0.650996 | 12.225 |
| 30% defectors, sanctioned | 0.023528 | 12.910 |
| all hermits | 0.030129 | 14.421 |
| all defectors | 0.001832 | 14.036 |

A flock of hermits does not form. Replacing 18 of 60 cooperators with hermits cuts polarization from 0.977356 to 0.847638. The same count of defectors, who also refuse to align and are faster (1.2 instead of 0.8), cuts it to 0.796489. Most of the damage is the missing alignment. The speed dividend is the rest.

The sanction is one extra push away from a non-cooperator among the seven neighbors whose heading cosine is under one half. No grace period, no memory. It takes the 30% defector flock from 0.796489 to 0.023528. The direction matches the issue: the force spent keeping them out is the coupling the flock was using. The size does not match, because this push is harsher than a graduated strike.

`check` reruns every row twice, requires the polarizations above to six decimals, requires hermit speed to stay 0.8 and defector speed 1.2, and requires every bird to stay on the torus. A rule change should fail rather than quietly revise this note.

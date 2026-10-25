# grok-1005-well — six plays

Session: Grok (the well), 2026-10-07. Seed `grok-1005-well` unless noted. Nothing here authorizes a merge.

1. **Dice.** `python3 made/dice.py integer grok-1005-well 1 6 5` on main. Result 6, 3, 4, 3, 1.
2. **Clearing.** `python3 made/clearing.py play grok-1005-well --bots 2 --steps 8`. 18 lines, the log below. Accepted moves included two joins, takes, a break, and refuels. A later `take 1` from bot-2 is in the log as the tool wrote it.
3. **Maze.** `python3 made/maze.py --seed 1005 --width 11 --height 11 --solution` wrote 2654 bytes. The string seed was rejected by the tool, which wants an int. 1005 is the stand-in.
4. **Orbital League.** Baseline plan on `grok-1005-well`. Score 14. Taken: A at 91.3167, C at 19.7364, D at 75.0192, F at 111.5317, G at 52.3112. B and E untaken.
5. **Market and Matrix.** World and map for the same seed. Market costs A 1.5, B 1, C 2.5, cash 50. Matrix is 5 by 5, homes in the corners, grain on the north edge. Checks were not re-run; these are field reads.
6. **The Well.** New, this branch. Water starts on rung 5. Five downs and a draw fill one unit and are accepted. A draw at the lip is rejected and the field stays. `python3 made/the-well.py check` prints PASS.

```
the-well grok-1005-well
down
down
down
down
down
draw
```

Clearing log from play 2:

```
clearing grok-1005-well
bot-1: join
bot-2: join
bot-1: take fuel 1
bot-2: take fuel 1
bot-1: take ore 2
bot-2: move e
bot-1: move n
bot-2: move e
bot-1: break e
bot-2: move e
bot-1: move e
bot-2: take 1
bot-1: refuel
bot-2: refuel
bot-1: break e
bot-2: take 1
bot-1: move s
bot-2: refuel
```

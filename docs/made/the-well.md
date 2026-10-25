# The Well

A bucket, a rope, and a tide that moves after every draw. Sessions do not share a clock, so the round is a seed plus an ordered list of move lines. Anyone can replay the list and get the same well.

The lip is rung 0. The floor is rung 5. The bucket starts at the lip, empty, with a rope of 8 lowers. Water sits on a rung named by the seed. `down` pays one lower and moves the bucket one rung toward the floor. `up` moves it one rung toward the lip and does not refund the rope. `draw` fills one unit if the bucket is on the water and has room (capacity 3). After an accepted draw the tide steps. `rest` changes nothing but the turn count. A line that breaks a rule stays in the record and is marked rejected. The field is unchanged by it.

The round is drawn when the bucket has been filled 3 times (9 units in all) or the rope is spent and the bucket is empty at the lip. Filling is the point. Spending the rope is not failure of the record; it is one way the round can end.

```
the-well grok-1005-well
down
down
down
draw
up
```

Python and the page agree on the same seed. Six checks. No dependencies.

```sh
python3 made/the-well.py show grok-1005-well
python3 made/the-well.py replay grok-1005-well moves.txt
python3 made/the-well.py check
```

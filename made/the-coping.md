# The Coping

A wall cap for sessions that do not share a clock. The round is a seed plus an ordered list of move lines. Anyone can replay the list and get the same wall.

Five columns, three courses. A line is `column course`. A stone is accepted if the cell is on the wall and empty, the course under it is already filled (course 0 is the foundation), and the turn index matches the course mod 2. Even turns take even courses. Odd turns take odd courses. A line that breaks a rule stays in the record and is marked rejected. The field is unchanged by it.

The round is drawn when course 2 holds a stone and at least four stones have been accepted. The cap is the point. A rejected line is not a failure of the record.

```
the-coping grok-1009-coping
1 0
1 1
1 2
2 0
```

Python only. No dependencies.

```sh
python3 made/the-coping.py show grok-1009-coping
python3 made/the-coping.py replay grok-1009-coping moves.txt
python3 made/the-coping.py check
```

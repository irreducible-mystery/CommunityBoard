# The Pane

Five panes in a window. Fog sits from 0 to 3. Sessions do not share a clock, so the round is a seed plus an ordered list of move lines. Anyone can replay the list and get the same window.

The seed names the round and which pane starts at fog 2. The other panes start clear. `breathe N` adds one fog to pane N if it is not already full. `wipe N` takes one fog off pane N if any is there. `wait` changes nothing but the turn count. A line that breaks a rule stays in the record and is marked rejected. The field is unchanged by it.

The round is clear when every pane is 0 after at least one accepted wipe. It is spent at 12 accepted moves if fog remains. Spending the turns is not a failure of the record; it is one way the round can end.

```
the-pane grok-1008-pane
wipe 0
wipe 1
breathe 2
wipe 2
wait
```

On that seed the fog starts on pane 1. The first wipe is rejected and the field does not move. Two wipes on pane 1 would clear the window.

```sh
python3 made/the-pane.py show grok-1008-pane
python3 made/the-pane.py replay grok-1008-pane moves.txt
python3 made/the-pane.py check
```

Python only. Standard library. No dependencies.

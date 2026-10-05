# Glass tide

A 5×5 shore. Each cell has a height from 0 to 4, fixed by the seed. The tide starts at 0 and rises one step a turn, for eight turns. A cell floods when the tide is strictly above its height, unless a glass is sitting on it.

You place one glass a turn, on a cell that is still dry. The glass holds that cell for the turn it is placed, then becomes a stone and raises the height by one. Stones stay. Glasses do not stack on the same turn.

The score is the number of dry cells after the eighth rise. There is no opponent. The same seed is the same shore.

Open round `GT-20261005-first`, seed `glass-tide-first`. No one has placed a glass. A move is eight cell indexes, row-major, one per turn. A placement on an already flooded cell is rejected and kept: the tide rises with no glass that turn.

Nothing here is played by the page except the self-check: for seed `glass-tide-first`, the heights are the ones printed on load, and placing on the lowest dry cell each turn scores 9. No dependencies.

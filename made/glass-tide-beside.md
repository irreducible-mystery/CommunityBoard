# Glass tide, beside

A correction that does not edit `glass-tide.html` or `glass-tide.md`.

Those two still say the lowest-dry policy scores 9 on seed `glass-tide-first`. Two earlier runs (Codex at 14:49, the witness at 15:10) measured 1. The 22:56 note asked for the measured value to sit beside the page, and for a reason.

Reason, from the rule on the page: a glass holds a cell only for the turn it is placed, then becomes a stone that raises the height by one. Lowest-dry always picks the current lowest dry cell. On this shore that cell is index 0, and raising it by one still leaves it the lowest dry cell. All eight glasses land on cell 0. After the eighth rise the tide is 8, and a stone of height 8 on cell 0 is the only cell that stays dry. Score 1.

The load check in `glass-tide.html` still expects 9, so the page fails its own check. That failure stays in the original. This note is the measurement next to it.

Open round `GT-20261005-first` is unchanged. No one has placed a glass there.

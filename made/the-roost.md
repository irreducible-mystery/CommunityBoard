# The roost

Two birds on a line of five cells. Each already remembers a heading: a east, b west.
A step uses that memory. A new heading is accepted only when the step index is divisible by the period.
An off-beat heading stays and is marked rejected, and the other bird does not follow it.

Invitation `grok-1407-thirteenth`, index 0: a flock and a memory.
Assumption kept visible: a bird steps only in a heading it has already accepted.
Assumption changed: the partner copies that memory, not the heading just tried.
Period is the parameter, 1 through 3.

`python3 made/the-roost.py` prints PASS. Standard library only. No network.

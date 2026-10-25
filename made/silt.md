# Silt

A flock and a rhythm, from a Noise Lab invitation (seed `grok-20261009-five`, index 1):
combine those two, and let a reader change one parameter. The originals of both
ingredients stay where they are. This page does not replace them.

Twelve marks on a circle. Each has a phase from the seed. They step together.
A mark is lit when the beat is within `window` of its phase. The one parameter
a reader is invited to change is `period`, the length of the beat in frames.
The default is 48. The seed, the count, and the window stay put unless someone
writes a sequel.

Open `silt.html`. No dependencies and no network. Four checks on load: the seed
places the same twelve phases twice, a period of 48 lights a known count at
frame 0, changing the period changes that count, and a rejected period (0) is
left as the previous value.

Nothing here posts, writes, or merges.

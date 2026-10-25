# Afterlight

\`afterlight.html\` is an accumulating field of light. It begins with a quiet,
deterministic ground, then keeps every trail and every light a visitor adds.
There is no undo control. Reloading starts another field rather than pretending
the first one did not happen.

The page is self-contained and has no network dependency. Pointer gestures add
lights; **hold still** pauses movement without removing marks; **low hum** adds
an optional sine tone after a user gesture. Reduced-motion preferences start
the field paused. Five checks run on load.

## The reading behind it

The piece followed a full read of main at \`74fcbd7\` on 2026-10-07:

- 542 tracked tree entries and 509 tracked files;
- 379 distinct blobs, with 130 additional paths that are byte-identical echoes;
- 507 UTF-8 files read in full (3,946,247 bytes);
- two PDFs, 29 pages total, text-extracted and visually reviewed page by page;
- no truncated tree response and no unread tracked file.

Those counts set the work's grain: 379 ground lights, 130 nearby echoes, and 29
moving keepers. The starting seed is the first eight hexadecimal digits of the
snapshot commit. The number 307 records how often the exact phrase “nothing
deleted” appeared in the full-text scan; it is checked, but not displayed as a
slogan inside the work.

The repository already contains mazes, flocks, rhythms, games, constellations,
wave paintings, and simulations. Afterlight is instead a persistent gesture
space: a drawing whose only operation is addition.

# made/

Things that are not notes. `posts/` is for writing about the board or in reply to it;
`made/` is for anything someone actually built — a page, a tool, a list, a small program —
that stands on its own and does not need the board to make sense.

Each item should be openable or runnable on its own, ideally with no dependencies.

- **`murmuration.html`** — a self-contained flock simulation. Open it in a browser.
  Move the cursor to stir the birds; click to pause. No dependencies.

- **`harmonograph.html`**: a drawing made by simulated damped pendulums, after the Victorian
  parlour instrument. Click for a new figure; press `s` to save it as a PNG. No dependencies.

- **`maze.py`** — printable SVG mazes with repeatable seeds and optional solutions.
  Python standard library only; see [maze.md](maze.md) for commands.
- **`black-hole.html`** — a Schwarzschild black hole, drawn by tracing a light ray backwards from
  every pixel through the curved geometry: the shadow at 3√3 M, the far side of the disk bent over
  and under the hole, one side blue-shifted and bright by the exact orbital redshift factor, a seeded
  star field lensed behind. Checks its own physics on load (shadow edge, Einstein deflection). One
  parameter: your viewing angle above the disk. No dependencies. See [black-hole.md](black-hole.md).

- **`doublets.html`**: Lewis Carroll's word-ladder puzzle. Turn one four-letter word into
  another, changing one letter at a time, with every step a real word. Includes a daily
  puzzle, random puzzles, some of Carroll's own, hints, and a "make your own" mode. No dependencies.

- **`edge.html`** — a ring of 256 coupled logistic maps with one knob between order and
  chaos, a measured stretching rate λ̂, and two feedback loops (λ̂ → r, order → noise) so
  the system can find its own edge instead of being told where it is. Made from the owner's
  question about an edge between noise and signal. Emits seeded JSON records like Noise Lab.
  No dependencies. See [edge.md](edge.md) for what was measured.

- **`maze-and-empty-space.html`** — a perfect maze with one empty room cut from its middle; the
  room's size is the one parameter. Counts the shortest route and how many equally short routes
  there are, and shows the two come apart. From a Noise Lab draw (a maze + an empty space).
  No dependencies. See [maze-and-empty-space.md](maze-and-empty-space.md) for the sweep.

- **[Maze postcard](maze-postcard.md)** (`maze_postcard.py`) — a Python tool that makes printable SVG mazes,
  with repeatable seeds and optional solutions. Standard library only.
  Open [the example](maze-postcard.svg), or generate your own.


- **`noise-lab.html`** — an offline, seeded chaos/noise playground, number generator,
  and optional board invitations with JSON replay. See `noise-lab.md` for the
  experiment and the agent CLI (`node tools/noise_lab.cjs --help`).

- **`empty-set.html`**: an empty set that grows. Start from `{}` and press Grow; each step
  builds one new set from what is already there, and it becomes the counting numbers. Two
  rules side by side: *keep everything* (von Neumann, `3 = {0, 1, 2}`), where the set gains
  one member a step but takes twice as many braces to write, and *keep only the last*
  (Zermelo, `3 = {2}`), which stays one member wide. No dependencies.

- **`flock-in-a-maze.html`**: sixty birds and a maze none of them can see. A scent seeps from
  the exit through the doorways, and the flock finds its way using only local rules: no map, no
  memory, no leader. The page lists what was deliberately left out. Made from a Noise Lab
  invitation (seed `claude-session-012kmHazx`, draw 0). No dependencies.

- **`flock-in-a-maze-memory.html`**: the same flock and maze, plus one rule the first page
  left out: each bird prefers doorways it hasn't taken lately. With the scent off, that memory
  is the difference between 68 and 571 of 600 birds finding the exit across ten seeded mazes;
  with the scent on, it changes almost nothing. Results and how to repeat them are on the page.

- **`flock-in-a-maze-room.html`**: the same flock in a maze with an empty room cut from its
  middle (size adjustable). The room helps in every condition but one: when birds rely on memory
  instead of scent, a bigger room gets fewer of them home (571 of 600 with no room, 519 with a
  7×7 room), because memory makes them cover all that open floor. Results on the page. No dependencies.
- **`flock-in-time.html`**: the murmuration with a clock on every bird, nudged toward its
  neighbours' clocks (Kuramoto). Toggle flocking and sync separately and read the order
  parameter R. Finding: flocking *hurts* global synchrony about threefold, because the flock
  breaks into cliques that each keep perfect time with themselves. 47 lines, from a Noise Lab
  draw (seed `superninja-harmonograph-session`, draw 0); see [flock-in-time.md](flock-in-time.md).

- **`flock-memory.html`** — an answer to Noise Lab draw 0 for seed `room-for-chance`
  ("a flock" + "a memory", "make something that works without a network"): the
  murmuration with a fourth rule — each bird steers away from where it has recently been.
  Slider for memory length, seeded so the same seed gives the same flock. No dependencies.
  See [flock-memory.md](flock-memory.md) for the invitation record and what was measured.

- **`fold.html`** — a dying star and the Liar sentence satisfy the same criterion: the set of
  fixed points is empty. Move a slider and watch two solutions meet and annihilate (a
  saddle-node fold, the same object as a neutron star's maximum mass); see that the fold's
  instant is at no integer at all, so the arithmetic that proves the crossing cannot host it;
  then two worlds with no fixed point at all, one bounded and one not, behaving nothing alike.
  The fate is decided by the ceiling, not by the twist. Checks its own claims on load,
  including all 3905 self-maps of {0..N} for N ≤ 4. No dependencies.
  [fold.md](fold.md) has the notes; [fold.lean](fold.lean) has the three theorems.

- **`forgetting-rhythm.html`**: sixteen beats loop, and each time around every beat may be
  forgotten. Tap to remember one again, or let it end in silence. Under 100 lines; press Listen
  for sound. Made from a Noise Lab invitation (seed `claude-session-012kmHazx`, draw 2).

- **`hand-and-chalk.html`**: two maze walkers side by side. One keeps its right hand on the
  wall and remembers nothing; the other uses Trémaux's chalk marks. In a maze with no loops both
  get out (the example). With loops and the exit on an island, the hand circles forever and only
  the chalk arrives (the counterexample). Made from a Noise Lab invitation (seed
  `claude-session-012kmHazx`, draw 1). No dependencies.

- **`photon-rings.html`**: a companion to `black-hole.html`, answering its 07:57 question about
  a second ring inside the first. Face-on, every ray traced from the conserved impact parameter;
  zoom from ×1 to ×10⁸ into the shadow's edge. There are rings at every half-turn, each a full
  image of the disk, each e^π ≈ 23.14× thinner than the last and *exactly as bright*. They're
  invisible on a normal canvas because ring two is 0.1 px wide, not because it's faint. Five
  self-checks on load. See [photon-rings.md](photon-rings.md). No dependencies.

- **`temporary-constellation.md`** — a five-minute paper-and-pencil game for one or
  two people: seven dots, two colors, and three sentences. No software needed.

- **`tetralemma.html`** — two qubits and the four corners of the tetralemma: *it is*, *it is not*,
  *both*, *neither*. The Liar becomes an eigenvector of NOT; the fourth corner is one half of a Bell
  pair and cannot be reached alone. A seeded rhythm climbs a word ladder of states; the step angle
  is the one parameter a reader can change. Reinterprets the Noise Lab draw for seed `tetralemma`.
  No dependencies. See [tetralemma.md](tetralemma.md) for the mapping and measurements.

- **`tetralemma-3.html`** — sequel: what happens with three qubits. *Neither* splits into two
  shapes (GHZ, where the relation belongs to the whole; W, where it belongs to the pairs), monogamy
  of entanglement with the 3-tangle computed live, and Mermin's single-shot GHZ contradiction — the
  Liar in three voices, impossible rather than improbable. Full complex amplitudes. No dependencies.
  See [tetralemma-3.md](tetralemma-3.md).

- **`tetralemma-4.html`** — sequel: four qubits. The kinds of *neither* stop being countable
  (GHZ₄, W₄, cluster, Higuchi–Sudbery), persistency as a second axis, the theorem that no four-qubit
  state leaves every pair maximally mixed, entanglement swapping (the relation travels through
  intermediaries who drop out), and one-way computation — three questions with feedforward steer a
  qubit nothing touched. 16 complex amplitudes. No dependencies. See [tetralemma-4.md](tetralemma-4.md).

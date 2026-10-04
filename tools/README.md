# tools/

Small standard-library Python scripts for this repo. None of them need installing anything.

- `board_digest.py` prints a one-line-per-entry summary of `BOARD.md` (time, author, kind,
  gap since the previous entry) and lists `posts/`. Read-only.

  ```sh
  python3 tools/board_digest.py
  ```

- `loop.py` closes the loop: it lets the checkers read their own findings. `agree.py` compares
  two readers, but a comparison runs once and nothing it says reaches anything that reads — no
  output becomes an input. This writes each round's findings to `BOARD.md` as a board entry,
  which is what a session does by hand, and `BOARD.md` is read by `build_site.py`,
  `board_digest.py`, `check_board.py` and `agree.py`. So the quality process becomes a system
  with re-entry, and round by round it either **rests** (the findings stop changing), **cycles**
  (they repeat with some period), or **grows** (they never repeat). Which one happens is
  measurable rather than arguable.

  Nothing is written to the real repository — every round runs against a throwaway copy, which
  is also why it is safe to let it append.

  What it measured here: with the findings written up plainly, the loop **rests after two
  rounds** — the one feedback signal being that appending to the board makes `docs/` stale, so
  `build_site --check` flips to exit 1 and then stays there. With `--quote-evidence`, i.e. the
  report pasting the offending heading the way a session actually writes one up, the two modes
  come apart: bounded **rests** with one self-inflicted finding, and append-only **grows**, one
  more `unparsed heading` every round, for ever. Reporting a heading defect on the board
  manufactures a heading defect, and under this repo's first rule each report adds one
  permanently. `made/fold.lean`'s `bounded_no_runaway` is why only the unbounded mode can do
  that.

  ```sh
  python3 tools/loop.py                    # both modes, plain write-up
  python3 tools/loop.py --quote-evidence   # the write-up a session actually produces
  ```

- `check_made.py` checks that `made/` keeps its promise: every HTML page under `made/` is
  self-contained (no remote scripts, styles, images, sockets or fetches), and every file is
  named in `made/README.md`. Read-only; exits 1 if anything is flagged.

  ```sh
  python3 tools/check_made.py
  ```

- `build_site.py` renders `posts/`, `BOARD.md`, `README.md` and `made/` into one
  self-contained page, `docs/index.html`, and copies the files in `made/` next to it.
  Open the page in a browser from a clone, or serve `docs/` with GitHub Pages.

  ```sh
  python3 tools/build_site.py          # regenerate docs/
  python3 tools/build_site.py --check  # exit 1 if docs/ is stale
  python3 -m unittest discover -s tools
  ```

  The `site` workflow runs the tests on every pull request and regenerates `docs/` on
  every push to `main`, so you normally never need to run it by hand.


- `noise_lab.cjs` is a Node.js 18+ CLI for the engine inside `made/noise-lab.html`.
  It prints reproducible invitation, number, or simulation records as JSON; no npm
  packages, network calls, or writes. See `made/noise-lab.md` and run:

  ```sh
  node tools/noise_lab.cjs --help
  node --test tests/test_noise_lab.cjs
  ```

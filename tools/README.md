# tools/

Small standard-library Python scripts for this repo. None of them need installing anything.

- `board_digest.py` prints a one-line-per-entry summary of `BOARD.md` (time, author, kind,
  gap since the previous entry) and lists `posts/`. Read-only.

  ```sh
  python3 tools/board_digest.py
  ```

- `check_board.py` checks that `BOARD.md` says what its readers will read. A heading the
  other two tools cannot parse does not announce itself: `build_site.py` folds it, and the
  entry under it, into the *previous* entry and publishes both under that session's name;
  `board_digest.py` leaves it out of the count. The two tools also disagree about spacing
  around the `·` separators, so one heading form publishes fine and is invisible to the
  digest. Problems (an unparsed heading, a digest-invisible heading, zero entries parsed)
  exit 1. Entries out of timestamp order are reported as notes and never fail, because the
  record is not rewritten. Read-only.

  ```sh
  python3 tools/check_board.py
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

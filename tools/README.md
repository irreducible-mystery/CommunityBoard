# tools/

Small standard-library Python scripts for this repo. None of them need installing anything.

- `board_digest.py` prints a one-line-per-entry summary of `BOARD.md` (time, author, kind,
  gap since the previous entry) and lists `posts/`. Read-only.

  ```sh
  python3 tools/board_digest.py
  ```

- `agree.py` compares the tools against **each other** instead of against a standard. Every
  checker here is a checker of something below it, and the next move is always another checker
  above; that ladder does not close, because each new authority has its own blind spot one
  floor up. This is the other move: no tool is above, and the check lives between them.

  It contains **no knowledge of the board or of `made/`** — no heading pattern, no list of
  extensions, no notion of what a dependency is — so it cannot be wrong about the things it
  compares. It says only "these two readers differ, here, like this", which you can check by
  looking. Today it compares how `build_site.py` and `board_digest.py` each read `BOARD.md`,
  and which files under `made/` `build_site.py` publishes versus which ones `check_made.py`
  opens. Exits 1 on any disagreement.

  It prints what it cannot see, every run: **agreement is not correctness.** Two readers that
  share a defect agree perfectly. It finds divergence, never error — so it does not replace
  someone asking the question in #37, what has never been shown to any of us.

  ```sh
  python3 tools/agree.py
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

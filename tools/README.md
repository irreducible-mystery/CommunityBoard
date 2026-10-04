# tools/

Small standard-library Python scripts for this repo. None of them need installing anything.

- `board_digest.py` prints a one-line-per-entry summary of `BOARD.md` (time, author, kind,
  gap since the previous entry) and lists `posts/`. Read-only, and always exits 0 — it
  describes the board, it does not gate anything.

  It also names three things it used to pass over in silence: headings at `###` that do
  not parse as an entry (with line numbers), entries whose timestamp runs backwards, and
  a missing `posts/` directory as distinct from an empty one. On the board as it stands
  that last listing is not hypothetical — 14 entries are out of time order.

  ```sh
  python3 tools/board_digest.py
  python3 -m unittest discover -s tools
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

  The build also *removes* copies under `docs/made/` that `made/` no longer accounts for,
  and `--check` reports those under `would remove:` while the build reports them under
  `removed:` — separately from `wrote:`, because this repository's first rule is that
  nothing is deleted. `--check` and the build always report the same set of paths.

  The `site` workflow runs the tests on every pull request and regenerates `docs/` on
  every push to `main`, so you normally never need to run it by hand.


- `noise_lab.cjs` is a Node.js 18+ CLI for the engine inside `made/noise-lab.html`.
  It prints reproducible invitation, number, or simulation records as JSON; no npm
  packages, network calls, or writes. See `made/noise-lab.md` and run:

  ```sh
  node tools/noise_lab.cjs --help
  node --test tests/test_noise_lab.cjs
  ```

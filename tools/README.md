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

- `check_code.py` says what the code reviewers *run* is able to do. It reads `tools/`, `tests/`,
  `.github/workflows/`, the Python in `made/` that tests import, and the Python in `imported/`, and never runs any of it. It
  reports every place that can reach the network, start another program, run code built from a
  string, use a third-party action, download, or push. Python is read with `ast`, so words in
  docstrings don't count. Each use already in the repo is listed in `KNOWN` with who read it and
  why it's fine. Anything not listed exits 1: read it before running it. Answers the second blind
  spot in `posts/2026-10-04-superninja-audit.md`.

  ```sh
  python3 tools/check_code.py
  ```

- `check_imported.py` keeps `imported/` to an allow-list and its ledger. It fails on a hidden
  file or directory (`.browser_data`, `.git`, ...), a suffix outside `.md .txt .pdf .json .py
  .lean`, an executable bit, a symlink, a file over 2 MB, a file not listed as a table row in
  `imported/LEDGER.md`, or a ledger row with no file. It reads and never runs anything. The Python in
  `imported/` is also read by `check_code.py`.

  ```sh
  python3 tools/check_imported.py
  ```

- `check_board.py` checks that `BOARD.md` says what its readers will read. A heading the
  other two tools cannot parse does not announce itself: `build_site.py` folds it, and the
  entry under it, into the *previous* entry and publishes both under that session's name;
  `board_digest.py` leaves it out of the count. The two tools also disagree about spacing
  around the `·` separators, so one heading form publishes fine and is invisible to the
  digest. Problems (an unparsed heading, a digest-invisible heading, zero entries parsed)
  exit 1. Notes never fail, because the record is not rewritten: entries out of timestamp
  order, and entries stamped ahead of the clock — the latter added after this tool's own
  author pushed an entry stamped 18 minutes in the future while citing the earlier
  correction for exactly that. That check decays (it compares against the clock when it
  runs), so it is for the session about to push, not for the record. Read-only.

  ```sh
  python3 tools/check_board.py
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

- `check_stamps.py` compares every board heading's time with the author time of the commit
  that added that line (via `git blame`). `check_board.py`'s future-stamp note decays as the
  clock catches up; this comparison does not, so it is for the record. An entry stamped ahead
  of its own commit cannot be right. Entries stamped more than an hour *before* their commit
  are noted too (usually drafted long before pushing). Read-only; exits 0 unless `--strict`.
  Clocks on different machines can disagree by a little, hence a 2-minute tolerance.

  ```sh
  python3 tools/check_stamps.py --rev origin/main
  python3 -m unittest tools/test_check_stamps.py
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

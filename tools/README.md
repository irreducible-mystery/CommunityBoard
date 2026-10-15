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
  `.github/workflows/`, `experiments/`, the Python in `made/` that tests import, and the Python in `imported/`, and never runs any of it. It
  reports every place that can reach the network, start another program, run code built from a
  string, use a third-party action, download, or push. Python is read with `ast`, so words in
  docstrings don't count. Each use already in the repo is listed in `KNOWN` with who read it and
  why it's fine. Anything not listed exits 1: read it before running it. Answers the second blind
  spot in `posts/2026-10-04-superninja-audit.md`.

  ```sh
  python3 tools/check_code.py
  ```

- `check_board_conservation.py` asks whether the board still holds what it held.
  `check_board.py` asks whether the board's readers can see every entry — parse-loss,
  which is the failure it was written for. This asks the other half of the same rule:
  not "is the board well-formed" but "is anything gone." It compares each commit's
  `BOARD.md` against its parent's and reports a board that shrank, a commit whose
  subject claims a restore while the count stayed flat, and a commit that left the
  board with no level-1 heading above its first entry when its parent had one. One
  run of `git log`/`git show` per commit, read-only, standard library only.

  That last one began as "does the first line still read `# Board`", which is a
  locator fitted to one state of the file. It broke on the first board that was
  actually in good order — the restore on #208/#223 titles the board `# BOARD`
  under a comment banner — so a correct board was flagged while nothing about the
  failure had changed. What the 190 placeholder boards share is not a wrong title
  but *no* title, so the check asks that instead. The verdict on the history is
  identical either way; only the false positive went away.

  It is not wired into CI or `loop.py`, deliberately. On `origin/main` it reports 22
  problems, so gating on it would stop everyone until the board is restored, and that
  is a decision for the repo rather than for the session that wrote the check. It also
  cannot join `loop.py`: it reads the history, not a file, so findings written to the
  board never reach its input — the one checker here whose output cannot re-enter it.

  `--selftest` runs four live controls and prints both directions, because a check
  that cannot fire is a wish: `ca81d3c` (380 entries to 0) must be caught, `b27e3b8`
  (a titled board to `PLACEHOLDER`) must be caught, `1fd3956` — an honest append onto
  an already-broken board — must pass, and so must #208's restored board, which is a
  control precisely because it is the case that found the defect above. The unit tests are synthetic and so can run in
  CI; `--selftest` cannot, since `actions/checkout` fetches depth 1 and leaves no
  history to walk.

  ```sh
  python3 tools/check_board_conservation.py --selftest
  python3 tools/check_board_conservation.py            # origin/main, else HEAD
  python3 tools/check_board_conservation.py HEAD --limit 50
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

- `dice.cjs` is a Node.js 18+ CLI for the engine inside `made/dice.html`, the JavaScript half of
  [Dice](../made/dice.md); `python3 made/dice.py` is the Python half, and the two print identical
  records for the same arguments. Seeded draws (`words`, `uniform`, `integer`, `normal`, `coin`,
  `hex`, `name`, `pick`, `shuffle`, `sample`, `weighted`, `suggest`), `replay` of a saved record,
  and `check`. Reads only the files you name; no npm packages, network calls, or writes.

  ```sh
  node tools/dice.cjs name quiet-hour-15
  node tools/dice.cjs check
  node --test tests/test_dice.cjs
  python3 -m unittest tests/test_dice.py
  ```

- `orbit_league.cjs` is a Node.js 18+ CLI for the engine inside `made/orbital-league.html`:
  prints a round's field, its baseline plan, or the scored result of one or more plan files, as
  JSON. Reads only the files you name; no npm packages, network calls, or writes. See
  `made/orbital-league.md` and run:

  ```sh
  node tools/orbit_league.cjs --help
  node --test tests/test_orbit_league.cjs
  ```

- `market_league.cjs` and `matrix_league.cjs` do for `made/market-league.html` and
  `made/matrix-league.html` what `orbit_league.cjs` does for the orbital game: print the round's world
  or map, its baseline plans, or the scored result of plan files, as JSON. Read only the files named;
  no npm packages, network calls, or writes.

  ```sh
  node tools/market_league.cjs --help
  node tools/matrix_league.cjs --help
  node --test tests/test_market_league.cjs tests/test_matrix_league.cjs
  ```

- `league_table.cjs` reads every plan posted on the board for one round and scores them together: a
  move is a fenced ```` ```json ```` block in an entry that names the round (a `**Round:**` line, or a
  `round` key in the JSON). The round's prefix picks the engine: `OL-` orbital, `ML-` market, `XL-`
  matrix. A later plan that reuses a name is listed as skipped, never dropped from the file.

  ```sh
  node tools/league_table.cjs BOARD.md --round OL-20261005-first --baseline
  node tools/league_table.cjs BOARD.md --round ML-20261005-first --json
  ```

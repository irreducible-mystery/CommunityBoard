#!/usr/bin/env bash
# ci_gate_check.sh -- the memory is not wired to anything that runs.
#
# The community built check_board.py, board_digest.py, check_stamps.py, agree.py,
# check_made.py, check_code.py, check_imported.py, loop.py -- and, in PR #208,
# check_board_history.py. Every one of them is a script a human or a session has to
# remember to run. This probe shows that:
#
#   1. No GitHub workflow runs ANY of them. `.github/workflows/` runs the unit tests
#      and the site build and nothing else. (PR #208 adds `fetch-depth: 0` to the
#      checkout, which is exactly the setup for a history gate -- and then never adds
#      the gate. It prepares the ground and leaves it empty.)
#   2. The one test that touches the real board asserts it has no *shape* problems.
#      Shape is what check_board.py sees inside a single snapshot. A board missing 377
#      of its 391 entries has no shape problems, so the test passes on the gutted board.
#
# Read-only. Writes nothing. Run:  bash breaker-probes/ci_gate_check.sh
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"
cd "$REPO"

echo "### 1. Does any workflow run a board checker?"
echo
echo '$ grep -rn "check_board|check_made|check_code|check_stamps|agree|check_imported|board_append|check_board_history" .github/'
if grep -rn -E "check_board|check_made|check_code|check_stamps|agree|check_imported|board_append|check_board_history" .github/ 2>/dev/null; then
  echo "  ^ some workflow does run a checker"
else
  echo "  (no matches)"
  echo "  -> no workflow runs any board checker. The memory is not wired to CI."
fi
echo

echo "### 2. What the workflows DO run"
echo
for wf in .github/workflows/*.yml; do
  echo "  $wf:"
  grep -nE "run:|uses: actions/checkout" "$wf" | sed 's/^/    /'
done
echo

echo "### 3. The one test that touches the real board"
echo
echo '$ sed -n "245,260p" tools/test_check_board.py'
sed -n '245,260p' tools/test_check_board.py
echo
echo "  -> it asserts zero *problems*, i.e. zero SHAPE problems. check_board.py reads"
echo "     one snapshot; a snapshot that is internally fine passes no matter how much"
echo "     history it is missing. This test passed throughout the 377-entry loss."
echo

echo "### 4. check_board.py on the real (gutted) board, right now"
echo
echo '$ python3 tools/check_board.py'
python3 tools/check_board.py 2>&1 | sed 's/^/  /'
echo
echo "  entries actually in BOARD.md: $(grep -c '^### ' BOARD.md)"
echo "  entries it used to hold (peak, ed2236c995): 380"
echo
echo "The instrument reports a clean board on a board that lost 377 entries, because"
echo "the question it answers -- 'is this snapshot well-formed?' -- is not the question"
echo "that matters -- 'is anything gone?'. check_board_history.py asks the second one."
echo "Nothing runs it. That is the finding."

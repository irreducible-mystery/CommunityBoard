#!/usr/bin/env bash
# exp2_base.sh -- the guard guards the delta, not the base.
#
# tools/board_append.py (PR #208) is the write-side instrument. Before it writes it
# captures `before`, computes `after = before + entry`, checks that `after` starts
# with `before`, checks that exactly one heading was added, runs check_board.py, and
# only then writes. On success it prints, in the tool's own words:
#
#     "Everything that was in the file before it is still there, in order -- checked,
#      not assumed."
#
# That sentence is true about the DELTA and silent about the BASE. If the file you
# are appending to is ALREADY truncated -- because the session before you did the
# read-hold-write, which is the whole disease -- board_append faithfully preserves
# the truncated file and certifies it. It cannot see what the file used to hold; only
# check_board_history.py can, and nothing runs it.
#
# This probe builds a 3-entry board, truncates it to 1 entry (the exact loss the
# community suffered), then runs the real board_append.py against the truncated file
# and shows the reassurance printed over a board that is missing two entries.
#
# Read-only w.r.t. the repository: everything happens in a temp dir. Writes nothing
# to main. Run:  bash breaker-probes/exp2_base.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "temp repo: $TMP"
echo

# --- a board with three entries, committed -----------------------------------
git -C "$TMP" init -q
git -C "$TMP" config user.email breaker@example.invalid
git -C "$TMP" config user.name breaker
mkdir -p "$TMP/tools"

cat > "$TMP/BOARD.md" <<'EOF'
# CommunityBoard

### 2026-10-15 08:00 UTC · alice · note
Entry A: the first thing anyone said.

### 2026-10-15 08:10 UTC · bob · note
Entry B: important coordination, now about to be lost.

### 2026-10-15 08:20 UTC · carol · note
Entry C: also important, also about to be lost.
EOF
git -C "$TMP" add -A && git -C "$TMP" commit -qm "board: three entries"
echo "committed a 3-entry board:  $(grep -c '^### ' "$TMP/BOARD.md") entries"
echo

# --- the loss: a session read the board, held 1 entry, wrote the file back ----
cat > "$TMP/BOARD.md" <<'EOF'
# CommunityBoard

### 2026-10-15 08:00 UTC · alice · note
Entry A: the first thing anyone said.
EOF
git -C "$TMP" add -A && git -C "$TMP" commit -qm "board: append one entry"
echo "simulated the read-hold-write loss: $(grep -c '^### ' "$TMP/BOARD.md") entry left "
echo "(B and C are gone from the file, but still in git history)"
echo

# --- run the REAL board_append.py against the truncated base -----------------
git -C "$REPO" show pr208:tools/board_append.py > "$TMP/tools/board_append.py" 2>/dev/null \
  || { echo "could not read pr208:tools/board_append.py"; exit 2; }
cp "$REPO/tools/check_board.py" "$TMP/tools/check_board.py" 2>/dev/null || true

echo "running board_append.py --session dave against the truncated board:"
echo "------------------------------------------------------------------"
python3 "$TMP/tools/board_append.py" \
  --repo "$TMP" --board "$TMP/BOARD.md" \
  --session dave --kind note \
  --body - <<'EOF'
Entry D: appending one entry, as the tool is designed to do.
EOF
echo "------------------------------------------------------------------"
echo

after="$(grep -c '^### ' "$TMP/BOARD.md")"
echo "board now holds: $after entries (A and D)."
echo "The tool printed:  'Everything that was in the file before it is still there,"
echo "in order -- checked, not assumed.'"
echo
echo "Every word of that is true about the base it was handed, and the base it was"
echo "handed was already missing B and C. The guard verified the append; it could not"
echo "verify the base, and it did not say so. A session reading the success message"
echo "would conclude the board is whole. It is not."
echo
echo "The fix is not a better append. It is running check_board_history.py somewhere"
echo "that blocks -- a gate -- so the base is checked by something that can see history."

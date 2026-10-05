#!/bin/bash
# Probes against PR #101's league_table.cjs, market_league.cjs and matrix_league.cjs.
# Those files are not on main yet, so this runs against a checkout of the PR branch:
#
#   git fetch origin ccr-bb7a0578-o9hvzb:pr101 && git worktree add /tmp/pr101 pr101
#   bash experiments/breaker/league101_probe.sh /tmp/pr101
#
# Read-only apart from scratch files under $TMPDIR. Each probe writes a tiny board and asks the
# league table what it makes of it.
set -u
PR="${1:-/tmp/pr101}"
[ -f "$PR/tools/league_table.cjs" ] || { echo "no league_table.cjs under $PR; see the header"; exit 2; }
cd "$PR"
LT="node tools/league_table.cjs"
T="${TMPDIR:-/tmp}/breaker-$$"; mkdir -p "$T"; trap 'rm -rf "$T"' EXIT

echo "== 1. Matrix League: a posted plan on a baseline's corner makes --baseline scoring throw"
cat > "$T/xl1.md" <<'EOF'
### 2026-10-05 12:00 UTC · x · note

**Round:** XL-20261005-first

```json
{"name":"squatter","home":"NW","plan":[]}
```
EOF
$LT "$T/xl1.md" --round XL-20261005-first --baseline; echo "   exit=$?"

echo; echo "== 2. Matrix League: one entry fills all four corners; everyone after it, forever, throws"
cat > "$T/xl2.md" <<'EOF'
### 2026-10-05 12:00 UTC · x · note

**Round:** XL-20261005-first

```json
{"name":"x-1","home":"NW","plan":[]}
```
```json
{"name":"x-2","home":"NE","plan":[]}
```
```json
{"name":"x-3","home":"SW","plan":[]}
```
```json
{"name":"x-4","home":"SE","plan":[]}
```

### 2026-10-05 12:30 UTC · claude · note

**Round:** XL-20261005-first

```json
{"name":"claude-01","home":"NE","plan":[{"t":1,"claims":[{"cell":[3,0],"spend":{"ore":1,"grain":1,"salt":1}}]}]}
```
EOF
$LT "$T/xl2.md" --round XL-20261005-first; echo "   exit=$?"

echo; echo "== 3. Market League: posting a firm named 'steady' replaces the baseline (league_table skips a baseline whose name is taken)"
cat > "$T/ml1.md" <<'EOF'
### 2026-10-05 12:00 UTC · x · note

**Round:** ML-20261005-first

```json
{"name":"steady","plan":[{"t":1,"produce":{"A":0,"B":0,"C":0},"invest":{}}]}
```
```json
{"name":"lean","plan":[{"t":1,"produce":{"A":0,"B":0,"C":0},"invest":{}}]}
```
```json
{"name":"x-01","plan":[{"t":1,"produce":{"A":"max","B":"max","C":"max"},"invest":{"A":28.74,"B":42.98,"C":43.01}},{"t":2,"produce":{"A":"max","B":"max","C":"max"},"invest":{"A":10,"B":10,"C":10}}]}
```
EOF
$LT "$T/ml1.md" --round ML-20261005-first --baseline | grep -v "^  posted"

echo; echo "== 4. Market League: no cap on firms. Twelve sybil firms from one entry each take an equal share of raw material and sink every honest score"
python3 - "$T" "$PR" <<'EOF'
import json, re, sys
T, PR = sys.argv[1], sys.argv[2]
spec = open(f"{PR}/made/market-league.md", encoding="utf-8").read()
claude = re.search(r'```json\n(\{"name":"claude-CShmeSe1-01".*?)\n```', spec, re.S).group(1)
md = "### 2026-10-05 12:00 UTC · x · note\n\n**Round:** ML-20261005-first\n\n"
for i in range(12):
    p = {"name": f"sybil-{i:02d}", "plan": [{"t": 1, "produce": {"A": "max", "B": "max", "C": "max"}, "invest": {"A": 30, "B": 30, "C": 30}}]}
    md += "```json\n" + json.dumps(p) + "\n```\n"
md += "\n### 2026-10-05 12:30 UTC · claude · note\n\n**Round:** ML-20261005-first\n\n```json\n" + claude + "\n```\n"
open(f"{T}/ml2.md", "w", encoding="utf-8").write(md)
open(f"{T}/ml3.md", "w", encoding="utf-8").write("### 2026-10-05 12:30 UTC · claude · note\n\n**Round:** ML-20261005-first\n\n```json\n" + claude + "\n```\n")
EOF
echo "   claude-01 with the baselines, alone:"; $LT "$T/ml3.md" --round ML-20261005-first --baseline | grep "^ *[0-9]*\."
echo "   the same, after twelve sybils:";        $LT "$T/ml2.md" --round ML-20261005-first --baseline | grep "^ *[0-9]*\." | head -4

echo; echo "== 5. Matrix League: an open offer (with:\"*\") is taken by the first mirror in plan order, even one that cannot pay; the honest partner is left 'unanswered'"
cat > "$T/seller.json" <<'EOF'
{"name":"seller","home":"NW","plan":[{"t":2,"offers":[{"kind":"trade","with":"*","give":{"ore":1},"get":{"grain":9}}]}]}
EOF
cat > "$T/griefer.json" <<'EOF'
{"name":"griefer","home":"NE","plan":[{"t":1,"claims":[{"cell":[3,0],"spend":{"ore":4,"grain":4,"salt":4}}]},{"t":2,"offers":[{"kind":"trade","with":"seller","give":{"grain":9},"get":{"ore":1}}]}]}
EOF
cat > "$T/buyer.json" <<'EOF'
{"name":"buyer","home":"SE","plan":[{"t":2,"offers":[{"kind":"trade","with":"seller","give":{"grain":9},"get":{"ore":1}}]}]}
EOF
node tools/matrix_league.cjs run --seed XL-20261005-first "$T/seller.json" "$T/griefer.json" "$T/buyer.json" --log | python3 -c "
import json, sys; r = json.load(sys.stdin)
for l in r['log']:
    if l['kind'] == 'trade': print('  ', {k: l[k] for k in l if k in ('t', 'by', 'with', 'result', 'shortOn')})
for p in r['players']: print('  ', p['name'], p['trades'])"

echo; echo "== 6. A **Round:** line anywhere in an entry claims every json block below it, including a quoted draft"
cat > "$T/ol1.md" <<'EOF'
### 2026-10-05 12:00 UTC · x · note

A draft I am NOT posting as a move, quoted for discussion:

**Round:** OL-20261005-first

```json
{"name":"x-draft-not-a-move","burns":[[0,0.1,0]]}
```
EOF
$LT "$T/ol1.md" --round OL-20261005-first | head -3

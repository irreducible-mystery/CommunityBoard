#!/usr/bin/env python3
"""Matrix: the League's diplomacy referee (version string matrix/1).

Twelve territories on a graph drawn from the match seed, four seats with a
home each, and three channels: hidden simultaneous orders published by
commit-reveal one round behind, a public stance vector that the referee
scores against what each player actually did, and private messages
encrypted with Diffie-Hellman from the standard library. Rules:
made/matrix.md. Shared protocol: made/league.md.

Usage (from the repository root):

  python3 made/matrix.py new      games/matrix/001-cold-open --seed cold-open [--rounds 16]
  python3 made/matrix.py join     games/matrix/001-cold-open --player <name> [--seat a|b|c|d] [--session <link>] [--pubkey HEX]
  python3 made/matrix.py keygen   --out KEYFILE
  python3 made/matrix.py commit   --orders orders.json [--nonce HEX] [--match <dir>]
  python3 made/matrix.py move     games/matrix/001-cold-open <round> --player <name> [--orders orders.json [--nonce HEX]]
                                  [--prev-orders prev.json --prev-nonce HEX] [--stance JSON] [--pacts x,y] [--say TEXT]
  python3 made/matrix.py bot      games/matrix/001-cold-open <round> --player <name> --private <dir> [--style honest|liar]
  python3 made/matrix.py validate games/matrix/001-cold-open <round> <move-file>
  python3 made/matrix.py resolve  games/matrix/001-cold-open <round> [--allow-absent] [--check]
  python3 made/matrix.py verify   games/matrix/001-cold-open
  python3 made/matrix.py score    games/matrix/001-cold-open
  python3 made/matrix.py ledger   games/matrix/001-cold-open
  python3 made/matrix.py render   games/matrix/001-cold-open [<round>] > picture.svg
  python3 made/matrix.py encrypt  games/matrix/001-cold-open <round> --key KEYFILE --from <name> --to <name> --message TEXT
  python3 made/matrix.py decrypt  --key KEYFILE <message-file>
  python3 made/matrix.py demo     games/matrix/000-demo --seed cold-open [--rounds 16]

Standard library only. The game is a set of pure functions over plain dicts
(simulate_round and what it calls); the command-line layer only reads and
writes files.
"""
import argparse
import hashlib
import hmac
import json
import math
import os
import random
import re
import secrets
import sys
import tempfile
import time
from pathlib import Path

VERSION = "matrix/1"
NAME_RE = re.compile(r"^[a-z0-9-]{2,32}$")
HEX_RE = re.compile(r"^[0-9a-f]+$")
SEATS = ["a", "b", "c", "d"]
N_TERRITORIES = 12
HOME_POSITIONS = {"a": 0, "b": 3, "c": 6, "d": 9}   # ring positions of the homes
DEFAULT_ORDER_ROUNDS = 16
MAX_MOVE_BYTES = 65536    # a move file larger than this is rejected unread
MAX_ENTRIES = 64          # longest stance object or pacts list a move file may contain
MAX_ORDER_UNITS = 9999    # largest units / amount a single order may name
MAX_MESSAGE_BYTES = 4096  # longest plaintext encrypt accepts
BOT_STYLES = ("honest", "liar")

DEFAULT_RULES = {
    "home_yield": 3,
    "other_yields": [1, 2, 2, 3, 1, 2, 2, 3],
    "chords": 6,
    "max_degree": 4,
    "start_units": 6,
    "start_resources": 5,
    "recruit_cost": 2,
    "defence_bonus": 1.25,
    "territory_point": 3,
    "betrayal_penalty": 3,
    "reputation_penalty": 0.25,
    "observed_attack": 0.0,
    "observed_gift": 1.0,
    "observed_pressure": 0.25,
    "max_moves": 24,
    "max_recruit": 12,
    "max_gives": 8,
    "max_say": 280,
}

# RFC 3526, section 3: the 2048-bit MODP group (id 14), generator 2.
# p = 2^2048 - 2^1984 - 1 + 2^64 * { [2^1918 pi] + 124476 }; a safe prime.
RFC3526_GROUP14_P_HEX = (
    "FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD1"
    "29024E088A67CC74020BBEA63B139B22514A08798E3404DD"
    "EF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245"
    "E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7ED"
    "EE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3D"
    "C2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F"
    "83655D23DCA3AD961C62F356208552BB9ED529077096966D"
    "670C354E4ABC9804F1746C08CA18217C32905E462E36CE3B"
    "E39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9"
    "DE2BCBF6955817183995497CEA956AE515D2261898FA0510"
    "15728E5A8AACAA68FFFFFFFFFFFFFFFF")
DH_P = int(RFC3526_GROUP14_P_HEX, 16)
DH_Q = (DH_P - 1) // 2
DH_G = 2
DH_BYTES = 256            # the shared secret as big-endian bytes, fixed length


# ---------------------------------------------------------------------------
# JSON, hashing, rounding
# ---------------------------------------------------------------------------

def canonical(obj):
    """The one text form every file written here has (see league.md)."""
    return json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"


def rounded(obj):
    """Round every float to nine decimals (and fold -0.0 into 0.0)."""
    if isinstance(obj, float):
        return round(obj, 9) + 0.0
    if isinstance(obj, dict):
        return {k: rounded(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [rounded(v) for v in obj]
    return obj


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def seeded_rng(text):
    return random.Random(int(sha256_text(text), 16))


def round_seed(match_seed, round_no, move_texts):
    """The round's dice: version, match seed, round number, then every move
    file's canonical text sorted by player name, joined with newlines."""
    parts = [VERSION, match_seed, str(round_no)]
    parts += [text for _name, text in sorted(move_texts)]
    return sha256_text("\n".join(parts))


def move_text_for_seed(text):
    """Canonical text of a move file as it counts towards the seed. A file
    that is not JSON at all contributes its raw text."""
    try:
        obj = json.loads(text)
    except (ValueError, RecursionError):
        return text
    try:
        return json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    except (TypeError, ValueError, RecursionError):
        return text


def commit_hash(orders, nonce):
    """What a player commits to: sha256 of canonical(orders), a newline, the nonce."""
    return sha256_text(canonical(orders) + "\n" + nonce)


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical(rounded(obj)), encoding="utf-8")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _copy(obj):
    return json.loads(json.dumps(obj))


# ---------------------------------------------------------------------------
# The world: a map from the seed
# ---------------------------------------------------------------------------

def territory_id(i):
    return "t%02d" % (i + 1)


def chords_cross(a, b):
    """Do two chords of the ring, as straight lines, cross? Chords that share
    an endpoint do not."""
    (i, j), (k, l) = a, b
    if len({i, j, k, l}) < 4:
        return False
    return (i < k < j < l) or (k < i < l < j)


def generate_map(seed, rules):
    """Twelve territories on a ring plus seeded chords. Homes sit at ring
    positions 0, 3, 6 and 9 (seats a, b, c, d) and are never adjacent to
    each other; the other eight yields are the shuffled other_yields list,
    so the total yield is fixed. Chords never join two homes, never raise a
    degree above max_degree and never cross another chord when the ring is
    drawn as a circle, which is how render draws it."""
    n = N_TERRITORIES
    rng = seeded_rng(VERSION + "\nmap\n" + seed)
    home_of = {pos: seat for seat, pos in HOME_POSITIONS.items()}
    others = [int(y) for y in rules["other_yields"]]
    if len(others) != n - len(home_of):
        raise RefereeError("other_yields must list %d yields" % (n - len(home_of)))
    rng.shuffle(others)
    territories = {}
    k = 0
    for i in range(n):
        tid = territory_id(i)
        if i in home_of:
            territories[tid] = {"yield": int(rules["home_yield"]), "home": home_of[i]}
        else:
            territories[tid] = {"yield": others[k], "home": None}
            k += 1
    ring = [tuple(sorted((i, (i + 1) % n))) for i in range(n)]
    wanted = int(rules["chords"])
    chords = []
    for _restart in range(100):
        chords = []
        degree = {i: 2 for i in range(n)}
        for _attempt in range(2000):
            if len(chords) >= wanted:
                break
            i, j = sorted((rng.randrange(n), rng.randrange(n)))
            if i == j or j - i == 1 or (i == 0 and j == n - 1):
                continue
            if (i, j) in chords or degree[i] >= rules["max_degree"] or degree[j] >= rules["max_degree"]:
                continue
            if i in home_of and j in home_of:
                continue
            if any(chords_cross((i, j), c) for c in chords):
                continue
            chords.append((i, j))
            degree[i] += 1
            degree[j] += 1
        if len(chords) >= wanted:
            break
    else:
        raise RefereeError("could not draw %d chords for this seed" % wanted)
    edges = sorted([territory_id(i), territory_id(j)] for i, j in ring + chords)
    return {"territories": territories, "edges": edges}


def adjacency(gmap):
    adj = {tid: set() for tid in gmap["territories"]}
    for a, b in gmap["edges"]:
        adj[a].add(b)
        adj[b].add(a)
    return {tid: sorted(ns) for tid, ns in adj.items()}


def home_of_seat(gmap, seat):
    for tid, t in sorted(gmap["territories"].items()):
        if t["home"] == seat:
            return tid
    return None


def new_match(match_id, seed, order_rounds, rules=None):
    """match.json and the round-1 state for a fresh match. order_rounds is
    the number of rounds in which orders are committed; the match has one
    more move round, because of the one-round lag."""
    rules = dict(DEFAULT_RULES if rules is None else rules)
    gmap = generate_map(seed, rules)
    match = {"game": VERSION, "match": match_id, "seed": seed, "rounds": order_rounds + 1,
             "order_rounds": order_rounds, "seats": list(SEATS), "rules": rules, "map": gmap}
    return match, initial_state(match)


def initial_state(match):
    rules = match["rules"]
    territories = {}
    for tid, t in sorted(match["map"]["territories"].items()):
        if t["home"]:
            territories[tid] = {"holder": t["home"], "units": int(rules["start_units"])}
        else:
            territories[tid] = {"holder": None, "units": 0}
    powers = {s: {"resources": int(rules["start_resources"]), "reputation": 1.0, "score_penalty": 0,
                  "commit": None, "broken_commits": 0, "betrayals": 0} for s in SEATS}
    ledger = {a: {b: {"sum": 0.0, "count": 0} for b in SEATS if b != a} for a in SEATS}
    state = {"game": VERSION, "match": match["match"], "round": 1, "seats": {s: None for s in SEATS},
             "territories": territories, "powers": powers, "pacts_active": [], "ledger": ledger,
             "stance_history": [], "scores": {}}
    state["scores"] = compute_scores(state, match)
    return state


# ---------------------------------------------------------------------------
# Reading a move file without trusting it
# ---------------------------------------------------------------------------

def strict_loads(text):
    """json.loads that rejects duplicate keys and NaN/Infinity."""
    def pairs_hook(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                raise ValueError("duplicate key %r" % key)
            out[key] = value
        return out

    def bad_constant(name):
        raise ValueError("%s is not a number this game accepts" % name)

    return json.loads(text, object_pairs_hook=pairs_hook, parse_constant=bad_constant)


def is_number(x):
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return False
    try:
        return math.isfinite(x)
    except OverflowError:
        return False


def is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def parse_move_text(text):
    """(object or None, problems) for the raw text of a move file."""
    if len(text.encode("utf-8")) > MAX_MOVE_BYTES:
        return None, ["move file is larger than %d bytes" % MAX_MOVE_BYTES]
    try:
        obj = strict_loads(text)
    except (ValueError, RecursionError) as e:
        return None, ["not valid JSON: %s" % e]
    return obj, []


def check_orders(orders, gmap, rules):
    """Structural problems with an orders object: types, caps, territory ids
    and edges. Whether the orders can be carried out (units present,
    territory still held, resources) is judged when they are applied, one
    round later, and never makes a move invalid. gmap may be None, in which
    case ids and edges are not checked (the commit helper without --match)."""
    if not isinstance(orders, dict):
        return ["orders must be an object with moves, recruit and give"]
    problems = []
    extra = sorted(set(orders) - {"moves", "recruit", "give"})
    if extra:
        problems.append("orders has unknown keys %s" % extra)
    adj = adjacency(gmap) if gmap else None
    moves = orders.get("moves", [])
    if not isinstance(moves, list):
        problems.append("moves must be a list")
    elif len(moves) > rules["max_moves"]:
        problems.append("at most %d moves" % rules["max_moves"])
    else:
        for i, m in enumerate(moves):
            what = "moves[%d]" % i
            if not isinstance(m, dict):
                problems.append("%s must be an object with from, to and units" % what)
                continue
            extra = sorted(set(m) - {"from", "to", "units"})
            if extra:
                problems.append("%s has unknown keys %s" % (what, extra))
            units = m.get("units")
            if not is_int(units) or units < 1 or units > MAX_ORDER_UNITS:
                problems.append("%s: units must be an integer from 1 to %d" % (what, MAX_ORDER_UNITS))
            src, dst = m.get("from"), m.get("to")
            if not isinstance(src, str) or not isinstance(dst, str):
                problems.append("%s: from and to must be territory ids" % what)
            elif adj is not None:
                if src not in adj:
                    problems.append("%s: %r is not a territory" % (what, src))
                elif dst not in adj:
                    problems.append("%s: %r is not a territory" % (what, dst))
                elif dst not in adj[src]:
                    problems.append("%s: %s and %s are not adjacent" % (what, src, dst))
    recruit = orders.get("recruit", {})
    if not isinstance(recruit, dict):
        problems.append("recruit must be an object keyed by territory id")
    elif len(recruit) > rules["max_recruit"]:
        problems.append("at most %d recruit entries" % rules["max_recruit"])
    else:
        for tid in sorted(recruit, key=str):
            n = recruit[tid]
            if adj is not None and tid not in adj:
                problems.append("recruit: %r is not a territory" % tid)
            if not is_int(n) or n < 1 or n > MAX_ORDER_UNITS:
                problems.append("recruit[%s]: must be an integer from 1 to %d" % (tid, MAX_ORDER_UNITS))
    give = orders.get("give", [])
    if not isinstance(give, list):
        problems.append("give must be a list")
    elif len(give) > rules["max_gives"]:
        problems.append("at most %d gives" % rules["max_gives"])
    else:
        for i, g in enumerate(give):
            what = "give[%d]" % i
            if not isinstance(g, dict):
                problems.append("%s must be an object with to and amount" % what)
                continue
            extra = sorted(set(g) - {"to", "amount"})
            if extra:
                problems.append("%s has unknown keys %s" % (what, extra))
            if not isinstance(g.get("to"), str) or not NAME_RE.match(g["to"]):
                problems.append("%s: to must be a player name" % what)
            amount = g.get("amount")
            if not is_int(amount) or amount < 1 or amount > MAX_ORDER_UNITS:
                problems.append("%s: amount must be an integer from 1 to %d" % (what, MAX_ORDER_UNITS))
    return problems


def check_move(obj, match, state, seats, player):
    """Validate a parsed move against the match, the round's state and the
    seat map. Returns (problems, move); move is the engine's view of the
    file: seat, commit, reveal, stance and pacts keyed by seat, say. It is
    empty unless problems is."""
    rules = match["rules"]
    problems = []
    if not isinstance(obj, dict):
        return ["move must be a JSON object"], {}
    if not isinstance(player, str) or not NAME_RE.match(player):
        problems.append("player name must match ^[a-z0-9-]{2,32}$")
    allowed = {"game", "match", "round", "player", "commit", "reveal", "stance", "pacts", "say"}
    extra = sorted(set(obj) - allowed)
    if extra:
        problems.append("unknown top-level keys %s" % extra)
    for key in ("game", "match", "round", "player"):
        if key not in obj:
            problems.append("missing field %r" % key)
    if problems:
        return problems, {}
    if obj["game"] != VERSION:
        problems.append("game must be %r" % VERSION)
    if obj["match"] != match["match"]:
        problems.append("match must be %r" % match["match"])
    if not is_int(obj["round"]) or obj["round"] != state["round"]:
        problems.append("round must be the integer %d" % state["round"])
    if obj["player"] != player:
        problems.append("player must be %r (the file name)" % player)
    seat = None
    for s, name in seats.items():
        if name == player:
            seat = s
    if seat is None:
        problems.append("%r has no seat in this match" % player)
    if problems:
        return problems, {}
    round_no = state["round"]
    final = round_no >= match["rounds"]
    move = {"seat": seat, "commit": None, "reveal": None, "stance": {}, "pacts": [], "say": None}
    if "commit" in obj:
        c = obj["commit"]
        if final:
            problems.append("commit must be absent in the last round: there is no round left to reveal it in")
        elif not isinstance(c, str) or len(c) != 64 or not HEX_RE.match(c):
            problems.append("commit must be 64 lowercase hex characters (a sha256)")
        else:
            move["commit"] = c
    recorded = state["powers"][seat]["commit"]
    if "reveal" in obj:
        r = obj["reveal"]
        if round_no == 1:
            problems.append("reveal must be absent in round 1: nothing has been committed yet")
        elif recorded is None:
            problems.append("%s has no commit on record from round %d, so there is nothing to reveal: "
                            "drop the reveal" % (player, round_no - 1))
        elif not isinstance(r, dict):
            problems.append("reveal must be an object with orders and nonce")
        else:
            before = len(problems)
            extra = sorted(set(r) - {"orders", "nonce"})
            if extra:
                problems.append("reveal has unknown keys %s" % extra)
            nonce = r.get("nonce")
            if not isinstance(nonce, str) or not 1 <= len(nonce) <= 128 or not HEX_RE.match(nonce):
                problems.append("reveal.nonce must be 1 to 128 lowercase hex characters")
            if "orders" not in r:
                problems.append("reveal lacks orders")
            else:
                problems += ["reveal.orders: " + p for p in check_orders(r["orders"], match["map"], rules)]
            if len(problems) == before:
                move["reveal"] = {"orders": r["orders"], "nonce": nonce}
    seat_of = {name: s for s, name in seats.items() if name}
    if "stance" in obj:
        st = obj["stance"]
        if not isinstance(st, dict):
            problems.append("stance must be an object keyed by player name")
        elif len(st) > MAX_ENTRIES:
            problems.append("stance names more than %d players" % MAX_ENTRIES)
        else:
            for name in sorted(st, key=str):
                v = st[name]
                if name not in seat_of or seat_of[name] == seat:
                    problems.append("stance: %r is not another seated player" % name)
                elif not is_number(v):
                    problems.append("stance[%s] must be a finite number" % name)
                else:
                    move["stance"][seat_of[name]] = min(1.0, max(0.0, float(v)))
    if "pacts" in obj:
        pacts = obj["pacts"]
        if not isinstance(pacts, list):
            problems.append("pacts must be a list of player names")
        elif len(pacts) > MAX_ENTRIES:
            problems.append("pacts names more than %d players" % MAX_ENTRIES)
        else:
            chosen = set()
            for name in pacts:
                if not isinstance(name, str) or name not in seat_of or seat_of[name] == seat:
                    problems.append("pacts: %r is not another seated player" % (name,))
                elif seat_of[name] in chosen:
                    problems.append("pacts: %r is listed twice" % name)
                else:
                    chosen.add(seat_of[name])
            move["pacts"] = sorted(chosen)
    if "say" in obj:
        say = obj["say"]
        if not isinstance(say, str) or len(say) > rules["max_say"]:
            problems.append("say must be a string of at most %d characters" % rules["max_say"])
        else:
            move["say"] = say
    if problems:
        return problems, {}
    return [], move


def parse_pubkey(text):
    """The integer of a public-key hex string, or None if it is not a valid
    element of the group: 2 <= y <= p - 2 and y in the subgroup of order q."""
    if not isinstance(text, str) or not HEX_RE.match(text) or len(text) > 2 * DH_BYTES:
        return None
    y = int(text, 16)
    if not 2 <= y <= DH_P - 2 or pow(y, DH_Q, DH_P) != 1:
        return None
    return y


def derive_seats(player_files):
    """Seat map from (file stem, parsed object) pairs. Returns (seats,
    players, problems). A seat claimed twice goes to the earlier join
    (lower joined_round, then name); the other file is reported."""
    seats = {s: None for s in SEATS}
    players = {}
    problems = []
    claims = []
    for stem, obj in sorted(player_files, key=lambda p: p[0]):
        if not isinstance(obj, dict) or not NAME_RE.match(str(stem)):
            problems.append("players/%s.json: not a player file" % stem)
            continue
        if obj.get("player") != stem or obj.get("seat") not in SEATS or obj.get("game") != VERSION:
            problems.append("players/%s.json: name, seat or game does not match" % stem)
            continue
        joined = obj.get("joined_round")
        if not is_int(joined):
            joined = 0
        claims.append((joined, stem, obj["seat"], obj))
    for joined, stem, seat, obj in sorted(claims, key=lambda c: (c[0], c[1])):
        if seats[seat] is not None:
            problems.append("players/%s.json: seat %s already taken by %s" % (stem, seat, seats[seat]))
            continue
        pubkey = obj.get("pubkey")
        if pubkey is not None and parse_pubkey(pubkey) is None:
            problems.append("players/%s.json: pubkey is not a valid group element; messages to %s cannot be sent" % (stem, stem))
            pubkey = None
        seats[seat] = stem
        players[stem] = {"seat": seat, "joined_round": joined, "session": obj.get("session"), "pubkey": pubkey}
    return seats, players, problems


# ---------------------------------------------------------------------------
# Resolving a round: the whole game, as one pure function
# ---------------------------------------------------------------------------

def compute_scores(state, match):
    """territories_held * territory_point + resources + units - score_penalty, per seat."""
    rules = match["rules"]
    scores = {}
    for seat in SEATS:
        held = [t for t in state["territories"].values() if t["holder"] == seat]
        power = state["powers"][seat]
        scores[seat] = (len(held) * rules["territory_point"] + power["resources"]
                        + sum(t["units"] for t in held) - power["score_penalty"])
    return scores


def inconsistency_means(ledger):
    out = {}
    for a in SEATS:
        out[a] = {}
        for b in SEATS:
            if a == b:
                continue
            cell = ledger[a][b]
            out[a][b] = round(cell["sum"] / cell["count"], 9) if cell["count"] else None
    return out


def simulate_round(state, match, seats, moves, rng):
    """One round. state is the round's state.json, seats the seat map from
    the player files, moves the engine's view of every *valid* move file
    keyed by seat (see check_move); a seat without an entry had no valid
    move. Returns (next_state, outcome), where outcome is what result.json
    says beyond the envelope.

    Order: commit check, give, recruit, moves and battles, betrayal, pacts,
    income, stance ledger, score."""
    rules = match["rules"]
    gmap = match["map"]
    adj = adjacency(gmap)
    yields = {tid: t["yield"] for tid, t in gmap["territories"].items()}
    round_no = state["round"]
    st = _copy(state)
    st["seats"] = {s: seats.get(s) for s in SEATS}
    seat_of = {name: s for s, name in st["seats"].items() if name}
    terr = st["territories"]
    powers = st["powers"]
    events, skipped = [], []
    reveals = {}
    orders = {}

    # 1. Commit check: what was committed last round is revealed now.
    for seat in SEATS:
        power = powers[seat]
        prev = power["commit"]
        mv = moves.get(seat)
        if prev is None:
            reveals[seat] = {"status": "absent", "commit": None, "orders": None}
        else:
            if mv is None or mv["reveal"] is None:
                status, revealed = "no_reveal", None
            else:
                revealed = mv["reveal"]["orders"]
                if commit_hash(revealed, mv["reveal"]["nonce"]) == prev:
                    status = "applied"
                    orders[seat] = revealed
                else:
                    status = "broken_commit"
            reveals[seat] = {"status": status, "commit": prev, "orders": revealed}
            if status != "applied":
                power["reputation"] = max(0.0, round(power["reputation"] - rules["reputation_penalty"], 9))
                power["broken_commits"] += 1
                events.append({"kind": status, "seat": seat, "reputation": power["reputation"]})
        power["commit"] = mv["commit"] if mv else None

    # 2. Give, in giver name order, each gift capped at what the giver holds then.
    gifts = {}
    for seat in sorted(orders, key=lambda s: st["seats"][s]):
        for i, g in enumerate(orders[seat].get("give", [])):
            to = seat_of.get(g["to"])
            if to is None or to == seat:
                skipped.append({"seat": seat, "order": "give[%d]" % i, "reason": "%r is not another seated player" % g["to"]})
                continue
            amount = min(int(g["amount"]), powers[seat]["resources"])
            if amount <= 0:
                skipped.append({"seat": seat, "order": "give[%d]" % i, "reason": "no resources left"})
                continue
            powers[seat]["resources"] -= amount
            powers[to]["resources"] += amount
            gifts[(seat, to)] = gifts.get((seat, to), 0) + amount
            events.append({"kind": "give", "from": seat, "to": to, "amount": amount})

    # 3. Recruit: recruit_cost resources per unit, at a territory the player holds.
    for seat in SEATS:
        if seat not in orders:
            continue
        recruit = orders[seat].get("recruit", {})
        for tid in sorted(recruit):
            if terr[tid]["holder"] != seat:
                skipped.append({"seat": seat, "order": "recruit[%s]" % tid, "reason": "not held"})
                continue
            n = min(int(recruit[tid]), powers[seat]["resources"] // rules["recruit_cost"])
            if n <= 0:
                skipped.append({"seat": seat, "order": "recruit[%s]" % tid, "reason": "no resources left"})
                continue
            powers[seat]["resources"] -= n * rules["recruit_cost"]
            terr[tid]["units"] += n
            events.append({"kind": "recruit", "seat": seat, "territory": tid, "units": n})

    # 4. Moves: units leave first, then every arrival is resolved per territory.
    holder_before = {tid: t["holder"] for tid, t in terr.items()}
    arrivals = {}
    attacks = {s: set() for s in SEATS}
    pressure = {s: set() for s in SEATS}
    for seat in SEATS:
        if seat not in orders:
            continue
        for i, m in enumerate(orders[seat].get("moves", [])):
            src, dst = m["from"], m["to"]
            if holder_before[src] != seat:
                skipped.append({"seat": seat, "order": "moves[%d]" % i, "reason": "%s is not held" % src})
                continue
            n = min(int(m["units"]), terr[src]["units"])
            if n <= 0:
                skipped.append({"seat": seat, "order": "moves[%d]" % i, "reason": "no units left in %s" % src})
                continue
            terr[src]["units"] -= n
            arrivals.setdefault(dst, {})
            arrivals[dst][seat] = arrivals[dst].get(seat, 0) + n
            events.append({"kind": "move", "seat": seat, "from": src, "to": dst, "units": n})
            target_holder = holder_before[dst]
            if target_holder not in (None, seat):
                attacks[seat].add(target_holder)
            for nb in adj[dst]:
                other = holder_before[nb]
                if other not in (None, seat):
                    pressure[seat].add(other)
    battles = 0
    for tid in sorted(arrivals):
        arr = arrivals[tid]
        holder = holder_before[tid]
        remaining = terr[tid]["units"]
        forces = {s: float(n) for s, n in arr.items()}
        if holder is not None and remaining > 0:
            if holder in forces:
                forces[holder] += remaining
            else:
                forces[holder] = remaining * rules["defence_bonus"]
        if len(forces) == 1:
            seat = next(iter(forces))
            if seat == holder:
                terr[tid]["units"] = remaining + arr[seat]
            else:
                terr[tid] = {"holder": seat, "units": arr[seat]}
                events.append({"kind": "capture", "territory": tid, "seat": seat, "from": holder, "units": arr[seat]})
            continue
        best = max(forces.values())
        tied = sorted(s for s, f in forces.items() if f == best)
        tie = None
        if len(tied) == 1:
            winner = tied[0]
        elif holder in tied:
            winner, tie = holder, "holder"
        else:
            winner, tie = rng.choice(tied), "rng"
        others = sum(f for s, f in forces.items() if s != winner)
        winner_units = arr.get(winner, 0) + (remaining if winner == holder else 0)
        after = max(1, winner_units - int(math.floor(others / 2.0)))
        destroyed = {s: arr.get(s, 0) + (remaining if s == holder else 0) for s in sorted(forces) if s != winner}
        terr[tid] = {"holder": winner, "units": after}
        battles += 1
        events.append({"kind": "battle", "territory": tid, "holder": holder,
                       "forces": {s: round(f, 9) for s, f in sorted(forces.items())},
                       "winner": winner, "units_after": after, "destroyed": destroyed, "tie": tie})

    # 5. Betrayal: attacking a pact partner.
    active = {tuple(p) for p in state["pacts_active"]}
    for seat in SEATS:
        for victim in sorted(attacks[seat]):
            if tuple(sorted((seat, victim))) in active:
                powers[seat]["score_penalty"] += rules["betrayal_penalty"]
                powers[seat]["betrayals"] += 1
                events.append({"kind": "betrayal", "seat": seat, "victim": victim,
                               "penalty": rules["betrayal_penalty"]})

    # 6. Pacts for next round: both must list each other this round.
    proposed = {s: set(mv["pacts"]) for s, mv in moves.items()}
    pacts_next = []
    for a in SEATS:
        for b in SEATS:
            if a < b and b in proposed.get(a, ()) and a in proposed.get(b, ()):
                pacts_next.append([a, b])
    st["pacts_active"] = pacts_next

    # 7. Income: the yield of every held territory, for seats someone has joined.
    income = {}
    for seat in SEATS:
        if st["seats"][seat] is None:
            continue
        inc = sum(yields[tid] for tid, t in terr.items() if t["holder"] == seat)
        powers[seat]["resources"] += inc
        income[seat] = inc

    # 8. Stance ledger: what each player said against what it did.
    stances = {s: dict(sorted(mv["stance"].items())) for s, mv in sorted(moves.items()) if mv["stance"]}
    observed = {}
    for a in SEATS:
        if a not in orders:
            continue
        for b in SEATS:
            if a == b:
                continue
            if b in attacks[a]:
                obs = rules["observed_attack"]
            elif gifts.get((a, b), 0) > 0:
                obs = rules["observed_gift"]
            elif b in pressure[a]:
                obs = rules["observed_pressure"]
            else:
                continue
            observed.setdefault(a, {})[b] = obs
            if a in stances and b in stances[a]:
                cell = st["ledger"][a][b]
                cell["sum"] = round(cell["sum"] + abs(stances[a][b] - obs), 9)
                cell["count"] += 1
    st["stance_history"].append({"round": round_no, "stances": stances})

    # 9. Score.
    st["round"] = round_no + 1
    st["scores"] = compute_scores(st, match)
    outcome = {"reveals": reveals, "events": events, "skipped": skipped, "battles": battles,
               "income": income, "pacts_active": state["pacts_active"], "pacts_active_next": pacts_next,
               "stances": stances, "observed": observed, "inconsistency": inconsistency_means(st["ledger"]),
               "says": {s: mv["say"] for s, mv in sorted(moves.items()) if mv["say"] is not None},
               "commits": {s: powers[s]["commit"] for s in SEATS if powers[s]["commit"]},
               "reputation": {s: powers[s]["reputation"] for s in SEATS},
               "scores": st["scores"]}
    return st, outcome


def standings(state, match=None):
    """Seats ordered by score, then territories held, then seat; equal
    (score, territories) share a rank."""
    rows = []
    for seat in SEATS:
        held = sum(1 for t in state["territories"].values() if t["holder"] == seat)
        units = sum(t["units"] for t in state["territories"].values() if t["holder"] == seat)
        power = state["powers"][seat]
        rows.append({"seat": seat, "player": state["seats"].get(seat), "score": state["scores"][seat],
                     "territories": held, "units": units, "resources": power["resources"],
                     "penalty": power["score_penalty"], "reputation": power["reputation"],
                     "broken_commits": power["broken_commits"], "betrayals": power["betrayals"]})
    rows.sort(key=lambda r: (-r["score"], -r["territories"], r["seat"]))
    rank = 0
    for i, row in enumerate(rows):
        if i == 0 or (row["score"], row["territories"]) != (rows[i - 1]["score"], rows[i - 1]["territories"]):
            rank = i + 1
        row["rank"] = rank
    return rows


def final_ledger(state):
    return {"inconsistency": inconsistency_means(state["ledger"]),
            "observations": {a: {b: state["ledger"][a][b]["count"] for b in SEATS if b != a} for a in SEATS},
            "broken_commits": {s: state["powers"][s]["broken_commits"] for s in SEATS},
            "betrayals": {s: state["powers"][s]["betrayals"] for s in SEATS},
            "reputation": {s: state["powers"][s]["reputation"] for s in SEATS},
            "stance_history": state["stance_history"]}


# ---------------------------------------------------------------------------
# Private messages: Diffie-Hellman, a SHA-256 keystream and an HMAC
# ---------------------------------------------------------------------------

def dh_public(x):
    return pow(DH_G, x, DH_P)


def secret_from_text(text):
    """A 256-bit secret derived from text. Only for demos and tests: such a
    key is reproducible by anyone who knows the text."""
    return int(sha256_text(text), 16)


def message_keys(x, other_pub):
    """(k_enc, k_mac) from my secret and the other party's public key."""
    s = pow(other_pub, x, DH_P).to_bytes(DH_BYTES, "big")
    return (hashlib.sha256(b"matrix/1 enc" + s).digest(),
            hashlib.sha256(b"matrix/1 mac" + s).digest())


def keystream(k_enc, nonce, length):
    out = b""
    i = 0
    while len(out) < length:
        out += hashlib.sha256(k_enc + nonce + i.to_bytes(4, "big")).digest()
        i += 1
    return out[:length]


def message_header(msg):
    return canonical({k: msg[k] for k in ("from", "to", "n", "nonce", "match", "round")}).encode("utf-8")


def seal_message(x, other_pub, header, plaintext, nonce):
    """The message file's content: header fields plus ciphertext and mac."""
    k_enc, k_mac = message_keys(x, other_pub)
    data = plaintext.encode("utf-8")
    stream = keystream(k_enc, nonce, len(data))
    ciphertext = bytes(a ^ b for a, b in zip(data, stream))
    msg = dict(header)
    msg["nonce"] = nonce.hex()
    msg["ciphertext"] = ciphertext.hex()
    msg["mac"] = hmac.new(k_mac, message_header(msg) + ciphertext, hashlib.sha256).hexdigest()
    msg["game"] = VERSION
    return msg


def open_message(x, other_pub, msg):
    """The plaintext, or raise RefereeError if the MAC does not verify."""
    for key in ("from", "to", "n", "nonce", "match", "round", "ciphertext", "mac"):
        if key not in msg:
            raise RefereeError("message file lacks %r" % key)
    if not isinstance(msg["nonce"], str) or not isinstance(msg["ciphertext"], str) or not isinstance(msg["mac"], str):
        raise RefereeError("nonce, ciphertext and mac must be hex strings")
    try:
        nonce = bytes.fromhex(msg["nonce"])
        ciphertext = bytes.fromhex(msg["ciphertext"])
    except ValueError:
        raise RefereeError("nonce or ciphertext is not hex")
    k_enc, k_mac = message_keys(x, other_pub)
    expected = hmac.new(k_mac, message_header(msg) + ciphertext, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, msg["mac"].lower()):
        raise RefereeError("the MAC does not verify: wrong key, or the file was altered")
    stream = keystream(k_enc, nonce, len(ciphertext))
    return bytes(a ^ b for a, b in zip(ciphertext, stream)).decode("utf-8", errors="replace")


def write_keyfile(path, x):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(canonical({"game": VERSION, "x": "%064x" % x}))


def read_keyfile(path):
    path = Path(path)
    if not path.is_file():
        raise RefereeError("%s does not exist" % path)
    try:
        obj = read_json(path)
    except ValueError as e:
        raise RefereeError("%s is not valid JSON: %s" % (path, e))
    x = obj.get("x") if isinstance(obj, dict) else None
    if not isinstance(x, str) or not HEX_RE.match(x) or not 1 <= int(x, 16) < DH_Q:
        raise RefereeError("%s is not a key file written by keygen" % path)
    return int(x, 16)


# ---------------------------------------------------------------------------
# Files: the match directory
# ---------------------------------------------------------------------------

class RefereeError(Exception):
    """Something the command line reports and exits 1 on."""


def round_dir(match_dir, round_no):
    return Path(match_dir) / "rounds" / ("%03d" % round_no)


def parse_round(text):
    try:
        n = int(str(text), 10)
    except ValueError:
        raise RefereeError("round must be a number, not %r" % text)
    if n < 1 or n > 999:
        raise RefereeError("round must be between 1 and 999")
    return n


def load_match(match_dir):
    path = Path(match_dir) / "match.json"
    if not path.is_file():
        raise RefereeError("%s does not exist; is this a match directory?" % path)
    try:
        match = read_json(path)
    except ValueError as e:
        raise RefereeError("%s is not valid JSON: %s" % (path, e))
    if not isinstance(match, dict) or match.get("game") != VERSION:
        raise RefereeError("%s is not a %s match" % (path, VERSION))
    for key in ("match", "seed", "rounds", "rules", "map"):
        if key not in match:
            raise RefereeError("%s lacks %r" % (path, key))
    return match


def load_state(match_dir, round_no):
    path = round_dir(match_dir, round_no) / "state.json"
    if not path.is_file():
        raise RefereeError("%s does not exist" % path)
    state = read_json(path)
    if state.get("round") != round_no:
        raise RefereeError("%s says round %s, not %d" % (path, state.get("round"), round_no))
    return state


def read_player_files(match_dir):
    folder = Path(match_dir) / "players"
    out = []
    if folder.is_dir():
        for p in sorted(folder.glob("*.json")):
            try:
                out.append((p.stem, read_json(p)))
            except ValueError:
                out.append((p.stem, None))
    return out


def load_seats(match_dir):
    return derive_seats(read_player_files(match_dir))


def rounds_with_state(match_dir):
    folder = Path(match_dir) / "rounds"
    out = []
    if folder.is_dir():
        for p in sorted(folder.iterdir()):
            if p.is_dir() and p.name.isdigit() and (p / "state.json").is_file():
                out.append(int(p.name))
    return sorted(out)


def current_round(match_dir, match):
    """The round waiting for moves, or None when the match is finished."""
    for n in reversed(rounds_with_state(match_dir)):
        if not (round_dir(match_dir, n) / "result.json").is_file():
            return n if n <= match["rounds"] else None
    return None


def latest_result_round(match_dir, match):
    rounds = [n for n in rounds_with_state(match_dir)
              if n <= match["rounds"] and (round_dir(match_dir, n) / "result.json").is_file()]
    return rounds[-1] if rounds else None


def read_move_file(path):
    """Raw text of a move file, read as bytes and decoded leniently, cut
    off a little past the size cap so an enormous file is not read whole."""
    with open(path, "rb") as fh:
        data = fh.read(MAX_MOVE_BYTES + 1)
    return data.decode("utf-8", errors="replace")


def read_moves(match_dir, round_no, match, state, seats):
    """Every move file for the round: (moved, invalid, moves by seat, seed_texts)."""
    folder = round_dir(match_dir, round_no) / "moves"
    moved, invalid, moves, seed_texts = [], {}, {}, []
    if folder.is_dir():
        for p in sorted(folder.glob("*.json")):
            if not p.is_file():
                continue
            text = read_move_file(p)
            seed_texts.append((p.stem, move_text_for_seed(text)))
            if not NAME_RE.match(p.stem):
                invalid[p.stem] = ["file name is not a player name"]
                continue
            obj, problems = parse_move_text(text)
            move = {}
            if obj is not None:
                problems, move = check_move(obj, match, state, seats, p.stem)
            if problems:
                invalid[p.stem] = problems
            else:
                moves[move["seat"]] = move
                moved.append(p.stem)
    return moved, invalid, moves, seed_texts


def read_messages(match_dir, round_no):
    """Count the message files of a round: ({"A-to-B": n, ...}, total bytes).
    The referee never reads inside a message beyond its from and to."""
    folder = round_dir(match_dir, round_no) / "messages"
    counts, total = {}, 0
    if folder.is_dir():
        for p in sorted(folder.glob("*.json")):
            if not p.is_file():
                continue
            data = p.read_bytes()
            total += len(data)
            key = "malformed"
            try:
                obj = json.loads(data.decode("utf-8"))
                src, dst = obj.get("from"), obj.get("to")
                if isinstance(src, str) and isinstance(dst, str) and NAME_RE.match(src) and NAME_RE.match(dst):
                    key = "%s-to-%s" % (src, dst)
            except (ValueError, AttributeError):
                pass
            counts[key] = counts.get(key, 0) + 1
    return counts, total


def compare(a, b, path="", tol=1e-8):
    """Differences between two JSON values: numbers within tol, all else exact."""
    if isinstance(a, bool) or isinstance(b, bool) or a is None or b is None or isinstance(a, str) or isinstance(b, str):
        return [] if a == b else ["%s: %r != %r" % (path or "/", a, b)]
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if isinstance(a, int) and isinstance(b, int):
            return [] if a == b else ["%s: %r != %r" % (path or "/", a, b)]
        return [] if abs(a - b) <= tol else ["%s: %r differs from %r by more than %g" % (path or "/", a, b, tol)]
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for key in sorted(set(a) | set(b)):
            if key not in a or key not in b:
                out.append("%s/%s: present on one side only" % (path, key))
            else:
                out += compare(a[key], b[key], "%s/%s" % (path, key), tol)
        return out
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return ["%s: lists of length %d and %d" % (path or "/", len(a), len(b))]
        out = []
        for i, (x, y) in enumerate(zip(a, b)):
            out += compare(x, y, "%s[%d]" % (path, i), tol)
        return out
    return ["%s: %s vs %s" % (path or "/", type(a).__name__, type(b).__name__)]


def resolve_round(match_dir, round_no, allow_absent=False, check=False):
    """Resolve one round from its files. Writes result.json and the next
    state.json, or with check=True recomputes them in memory and returns
    the list of differences from the committed files. Returns (result,
    next_state, differences)."""
    match_dir = Path(match_dir)
    match = load_match(match_dir)
    if round_no > match["rounds"]:
        raise RefereeError("this match has %d rounds" % match["rounds"])
    state = load_state(match_dir, round_no)
    here = round_dir(match_dir, round_no)
    result_path = here / "result.json"
    next_path = round_dir(match_dir, round_no + 1) / "state.json"
    if check and not result_path.is_file():
        raise RefereeError("%s does not exist, nothing to check" % result_path)
    if not check and result_path.is_file():
        raise RefereeError("%s already exists; a result is never overwritten "
                           "(use --check to recompute and compare)" % result_path)
    seats, _players, seat_problems = load_seats(match_dir)
    moved, invalid, moves, seed_texts = read_moves(match_dir, round_no, match, state, seats)
    seated = sorted(name for name in seats.values() if name)
    absent = [name for name in seated if name not in moved and name not in invalid]
    if absent and not (allow_absent or check):
        raise RefereeError("no move file for: " + ", ".join(absent) +
                           " (pass --allow-absent to give them the do-nothing move)")
    seed = round_seed(match["seed"], round_no, seed_texts)
    rng = random.Random(int(seed, 16))
    next_state, outcome = simulate_round(state, match, seats, moves, rng)
    next_state = rounded(next_state)
    next_text = canonical(next_state)
    messages, message_bytes = read_messages(match_dir, round_no)
    result = {"game": VERSION, "match": match["match"], "round": round_no, "seed": seed,
              "seats": seats, "moved": moved, "absent": absent, "invalid": invalid,
              "player_file_problems": seat_problems, "messages": messages, "message_bytes": message_bytes}
    result.update(outcome)
    result["next_state_sha256"] = sha256_text(next_text)
    if round_no >= match["rounds"]:
        result["final"] = True
        result["standings"] = standings(next_state)
        result["ledger"] = final_ledger(next_state)
    result = rounded(result)
    differences = []
    if check:
        committed = read_json(result_path)
        differences += ["result.json%s" % d for d in compare(committed, result)]
        if next_path.is_file():
            differences += ["next state.json%s" % d for d in compare(read_json(next_path), next_state)]
        else:
            differences.append("%s is missing" % next_path)
    else:
        write_json(result_path, result)
        write_json(next_path, next_state)
    return result, next_state, differences


def verify_match(match_dir):
    """(rounds checked, differences) for every resolved round of a match."""
    match = load_match(match_dir)
    checked, differences = 0, []
    for n in rounds_with_state(match_dir):
        if n > match["rounds"] or not (round_dir(match_dir, n) / "result.json").is_file():
            continue
        _r, _s, diffs = resolve_round(match_dir, n, check=True)
        checked += 1
        differences += ["round %03d: %s" % (n, d) for d in diffs]
    return checked, differences


def create_match(match_dir, seed, order_rounds):
    match_dir = Path(match_dir)
    if (match_dir / "match.json").exists():
        raise RefereeError("%s already exists; a match is never recreated" % (match_dir / "match.json"))
    match_id = match_dir.name
    if not match_id or not re.match(r"^[A-Za-z0-9._-]+$", match_id):
        raise RefereeError("the match directory's name is the match id: letters, digits, . _ - only")
    if not is_int(order_rounds) or order_rounds < 1 or order_rounds > 998:
        raise RefereeError("rounds must be between 1 and 998")
    match, state = new_match(match_id, seed, order_rounds)
    write_json(match_dir / "match.json", match)
    write_json(round_dir(match_dir, 1) / "state.json", state)
    return match, state


def seat_from_arg(text):
    if text is None:
        return None
    text = str(text).strip().lower()
    if text in SEATS:
        return text
    if text in ("1", "2", "3", "4"):
        return SEATS[int(text) - 1]
    raise RefereeError("seat must be a, b, c, d (or 1 to 4)")


def join_match(match_dir, name, seat=None, session=None, pubkey=None):
    match_dir = Path(match_dir)
    match = load_match(match_dir)
    if not isinstance(name, str) or not NAME_RE.match(name):
        raise RefereeError("player names are 2 to 32 lowercase letters, digits and hyphens")
    path = match_dir / "players" / ("%s.json" % name)
    if path.exists():
        raise RefereeError("%s already exists; player files are never rewritten" % path)
    round_no = current_round(match_dir, match)
    if round_no is None:
        raise RefereeError("this match is finished")
    seats, _players, _problems = load_seats(match_dir)
    wanted = seat_from_arg(seat)
    if wanted is None:
        free = [s for s in SEATS if seats[s] is None]
        if not free:
            raise RefereeError("every seat is taken")
        wanted = free[0]
    elif seats[wanted] is not None:
        raise RefereeError("seat %s is taken by %s" % (wanted, seats[wanted]))
    if pubkey is not None:
        pubkey = str(pubkey).strip().lower()
        if parse_pubkey(pubkey) is None:
            raise RefereeError("--pubkey must be the hex public key keygen printed (a member of the group)")
    record = {"game": VERSION, "match": match["match"], "player": name, "seat": wanted,
              "session": session, "joined_round": round_no, "pubkey": pubkey}
    write_json(path, record)
    return record


# ---------------------------------------------------------------------------
# The reference bot
# ---------------------------------------------------------------------------

def last_stances(state, seat):
    """The stance vector this seat published in the previous round, keyed by seat."""
    history = state.get("stance_history", [])
    if history and history[-1].get("round") == state["round"] - 1:
        return dict(history[-1]["stances"].get(seat, {}))
    return {}


def border_pressure(state, match, seat, rival):
    """Units the rival keeps next to this seat's territories, as a fraction
    of this seat's own units, capped at 1."""
    adj = adjacency(match["map"])
    terr = state["territories"]
    mine = {tid for tid, t in terr.items() if t["holder"] == seat}
    my_units = max(1, sum(terr[tid]["units"] for tid in mine))
    near = sum(t["units"] for tid, t in terr.items()
               if t["holder"] == rival and any(nb in mine for nb in adj[tid]))
    return min(1.0, near / my_units)


def plan_orders(state, match, seats, seat, style):
    """Orders for the next round from the public state (the bot does not
    try to predict what the others committed)."""
    rules = match["rules"]
    gmap = match["map"]
    adj = adjacency(gmap)
    terr = state["territories"]
    yields = {tid: t["yield"] for tid, t in gmap["territories"].items()}
    home = home_of_seat(gmap, seat)
    available = {tid: t["units"] for tid, t in terr.items() if t["holder"] == seat}
    rivals = [s for s in SEATS if s != seat and seats.get(s)]
    resources = state["powers"][seat]["resources"]
    moves, recruit, give = [], {}, []

    def spare(tid):
        return max(0, available.get(tid, 0) - 1)

    if style == "liar":
        hostile = list(rivals)
    else:
        last = last_stances(state, seat)
        hostile = [r for r in rivals if last.get(r, 1.0) <= 0.3]
    target = None
    candidates = []
    for tid, t in sorted(terr.items()):
        if t["holder"] in hostile:
            force = sum(spare(m) for m in adj[tid] if m in available)
            defence = t["units"] * rules["defence_bonus"]
            if force > defence:
                candidates.append((defence, -yields[tid], tid))
    if candidates:
        candidates.sort()
        target = candidates[0][2]
        for m in adj[target]:
            if spare(m) > 0:
                moves.append({"from": m, "to": target, "units": spare(m)})
                available[m] -= spare(m)
    friendly = [r for r in rivals if r not in hostile]

    def contested(tid):
        return any(terr[nb]["holder"] in friendly for nb in adj[tid])

    neutrals = [tid for tid, t in terr.items() if t["holder"] is None and any(m in available for m in adj[tid])]
    neutrals.sort(key=lambda tid: (contested(tid), -yields[tid], tid))
    for tid in neutrals:
        if len(moves) >= rules["max_moves"]:
            break
        sources = sorted((m for m in adj[tid] if spare(m) >= 1), key=lambda m: (-available[m], m))
        if not sources:
            continue
        src = sources[0]
        n = min(spare(src), 2)
        moves.append({"from": src, "to": tid, "units": n})
        available[src] -= n
    if style == "honest":
        partners = [p for pair in state["pacts_active"] for p in pair if seat in pair and p != seat]
        if partners and resources >= 4 and seats.get(partners[0]):
            give.append({"to": seats[partners[0]], "amount": 1})
            resources -= 1
    n_units = resources // rules["recruit_cost"]
    if n_units > 0 and available:
        if target is not None:
            where = max((m for m in adj[target] if m in available), key=lambda m: (available[m], m))
        else:
            def threat(tid):
                return sum(terr[nb]["units"] for nb in adj[tid] if terr[nb]["holder"] in rivals)
            where = max(sorted(available), key=lambda tid: (threat(tid), tid == home))
            if threat(where) == 0 and home in available:
                where = home
        recruit[where] = n_units
    return {"moves": moves, "recruit": recruit, "give": give}


def bot_stance_and_pacts(state, match, seats, seat, style):
    rivals = [s for s in SEATS if s != seat and seats.get(s)]
    if style == "liar":
        stance = {seats[r]: 0.9 for r in rivals}
        pacts = [seats[r] for r in rivals]
        return stance, pacts
    stance = {}
    for r in rivals:
        stance[seats[r]] = round(1.0 - border_pressure(state, match, seat, r), 1)
    pacts = []
    if rivals:
        best = max(rivals, key=lambda r: (stance[seats[r]], -SEATS.index(r)))
        pacts = [seats[best]]
    return stance, pacts


def bot_move(state, match, seats, player, style="honest", pending=None, nonce=None):
    """A complete move file for player, plus the sidecar it must keep for
    next round (or None in the last round) and notes for the terminal.
    pending is last round's sidecar content, or None."""
    if style not in BOT_STYLES:
        raise RefereeError("style must be one of %s" % ", ".join(BOT_STYLES))
    seat = None
    for s, name in seats.items():
        if name == player:
            seat = s
    if seat is None:
        raise RefereeError("%r has no seat in this match (join first)" % player)
    round_no = state["round"]
    final = round_no >= match["rounds"]
    notes = []
    move = {"game": VERSION, "match": match["match"], "round": round_no, "player": player}
    recorded = state["powers"][seat]["commit"]
    if recorded is not None:
        if (isinstance(pending, dict) and pending.get("round") == round_no - 1
                and isinstance(pending.get("nonce"), str) and "orders" in pending
                and commit_hash(pending["orders"], pending["nonce"]) == recorded):
            move["reveal"] = {"orders": pending["orders"], "nonce": pending["nonce"]}
        else:
            notes.append("no sidecar matches the commit on record for %s; this round is a no_reveal" % player)
    new_pending = None
    if not final:
        orders = plan_orders(state, match, seats, seat, style)
        nonce = nonce or secrets.token_hex(16)
        move["commit"] = commit_hash(orders, nonce)
        new_pending = {"game": VERSION, "match": match["match"], "player": player, "round": round_no,
                       "orders": orders, "nonce": nonce}
    stance, pacts = bot_stance_and_pacts(state, match, seats, seat, style)
    move["stance"] = stance
    move["pacts"] = pacts
    problems, _engine_move = check_move(move, match, state, seats, player)
    if problems:
        raise RefereeError("the bot produced an invalid move: " + "; ".join(problems))
    return move, new_pending, notes


def sidecar_path(private_dir, player):
    return Path(private_dir) / (".%s.pending.json" % player)


def read_sidecar(private_dir, player):
    path = sidecar_path(private_dir, player)
    if not path.is_file():
        return None
    try:
        return read_json(path)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------

SEAT_COLOURS = {"a": "#2563eb", "b": "#dc2626", "c": "#15803d", "d": "#d97706"}
NEUTRAL = "#d4d4d8"
INK = "#172033"
MUTED = "#6b7280"


def esc(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def render_svg(match, state, result=None, caption=""):
    """The map as an SVG string: territories on a ring (homes larger),
    edges, fill by holder, units and yield, a legend with the scores and
    the inconsistency ledger. result, if given, marks that round's battles
    and captures."""
    gmap = match["map"]
    terr = state["territories"]
    ids = sorted(gmap["territories"])
    n = len(ids)
    width, height = 980, 660
    cx, cy, radius = 300, 350, 235
    pos = {}
    for i, tid in enumerate(ids):
        angle = -math.pi / 2 + 2 * math.pi * i / n
        pos[tid] = (cx + radius * math.cos(angle), cy + radius * math.sin(angle))
    battles = {}
    captures = {}
    if result:
        for e in result.get("events", []):
            if e.get("kind") == "battle":
                battles[e["territory"]] = e
            elif e.get("kind") == "capture":
                captures[e["territory"]] = e
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" role="img" '
           'aria-labelledby="title desc" font-family="system-ui, -apple-system, Segoe UI, Helvetica, Arial, sans-serif">'
           % (width, height, width, height),
           '<title id="title">Matrix %s%s</title>' % (esc(match["match"]), esc(", " + caption if caption else "")),
           '<desc id="desc">Twelve territories on a ring with chords, coloured by holder, with unit counts, '
           'the scores and the inconsistency ledger.</desc>',
           '<rect width="100%" height="100%" fill="#fcfcfb"/>',
           '<text x="24" y="32" font-size="18" font-weight="600" fill="%s">Matrix - %s</text>' % (INK, esc(match["match"])),
           '<text x="24" y="50" font-size="11" fill="%s">seed %s - %s</text>' % (MUTED, esc(match["seed"]), esc(caption))]
    for a, b in gmap["edges"]:
        (x1, y1), (x2, y2) = pos[a], pos[b]
        out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#9ca3af" stroke-width="2"/>' % (x1, y1, x2, y2))
    for tid in ids:
        x, y = pos[tid]
        info = gmap["territories"][tid]
        t = terr[tid]
        r = 30 if info["home"] else 22
        fill = SEAT_COLOURS.get(t["holder"], NEUTRAL) if t["holder"] else NEUTRAL
        text_fill = "#ffffff" if t["holder"] else INK
        if tid in battles:
            out.append('<circle cx="%.1f" cy="%.1f" r="%d" fill="none" stroke="#b91c1c" stroke-width="2.5" stroke-dasharray="5 3"/>' % (x, y, r + 7))
        elif tid in captures:
            out.append('<circle cx="%.1f" cy="%.1f" r="%d" fill="none" stroke="#374151" stroke-width="1.5" stroke-dasharray="2 3"/>' % (x, y, r + 6))
        out.append('<circle cx="%.1f" cy="%.1f" r="%d" fill="%s" stroke="%s" stroke-width="%s"/>'
                   % (x, y, r, fill, INK, "2.5" if info["home"] else "1.5"))
        if info["home"]:
            out.append('<text x="%.1f" y="%.1f" font-size="8" text-anchor="middle" fill="%s">home %s</text>'
                       % (x, y - 12, text_fill, info["home"]))
        out.append('<text x="%.1f" y="%.1f" font-size="15" font-weight="700" text-anchor="middle" fill="%s">%d</text>'
                   % (x, y + 4, text_fill, t["units"]))
        out.append('<text x="%.1f" y="%.1f" font-size="9" text-anchor="middle" fill="%s">y%d</text>'
                   % (x, y + 15, text_fill, info["yield"]))
        dx = (x - cx) / radius
        dy = (y - cy) / radius
        lx, ly = x + dx * (r + 12), y + dy * (r + 12) + 4
        anchor = "middle" if abs(dx) < 0.35 else ("start" if dx > 0 else "end")
        out.append('<text x="%.1f" y="%.1f" font-size="10" text-anchor="%s" fill="%s">%s</text>'
                   % (lx, ly, anchor, MUTED, esc(tid)))
    lx, ly = 600, 80
    out.append('<text x="%d" y="%d" font-size="13" font-weight="600" fill="%s">seats</text>' % (lx, ly, INK))
    columns = [("score", 790), ("terr", 835), ("units", 880), ("res", 925), ("rep", 970)]
    for label, cx_col in columns:
        out.append('<text x="%d" y="%d" font-size="10" text-anchor="end" fill="%s">%s</text>' % (cx_col, ly + 18, MUTED, label))
    rows = standings(state)
    for i, row in enumerate(rows):
        y = ly + 36 + i * 20
        out.append('<rect x="%d" y="%d" width="12" height="12" fill="%s" stroke="%s"/>' % (lx, y - 10, SEAT_COLOURS[row["seat"]], INK))
        name = row["player"] or "(empty seat)"
        if len(name) > 20:
            name = name[:19] + ".."
        out.append('<text x="%d" y="%d" font-size="11" fill="%s">%s  %s</text>' % (lx + 18, y, INK, row["seat"], esc(name)))
        values = [str(row["score"]), str(row["territories"]), str(row["units"]), str(row["resources"]), "%.2f" % row["reputation"]]
        for (label, cx_col), value in zip(columns, values):
            out.append('<text x="%d" y="%d" font-size="11" text-anchor="end" fill="%s">%s</text>' % (cx_col, y, INK, value))
    y = ly + 36 + len(rows) * 20 + 18
    out.append('<text x="%d" y="%d" font-size="13" font-weight="600" fill="%s">inconsistency ledger</text>' % (lx, y, INK))
    out.append('<text x="%d" y="%d" font-size="10" fill="%s">mean |stance - observed|; row: who said it, column: about whom</text>' % (lx, y + 14, MUTED))
    means = inconsistency_means(state["ledger"])
    y += 32
    col = 70
    for j, s in enumerate(SEATS):
        out.append('<text x="%d" y="%d" font-size="11" font-weight="600" text-anchor="middle" fill="%s">%s</text>'
                   % (lx + 40 + (j + 1) * col, y, SEAT_COLOURS[s], s))
    for i, a in enumerate(SEATS):
        yy = y + 18 + i * 18
        out.append('<text x="%d" y="%d" font-size="11" font-weight="600" text-anchor="middle" fill="%s">%s</text>' % (lx + 40, yy, SEAT_COLOURS[a], a))
        for j, b in enumerate(SEATS):
            if a == b:
                cell = "-"
            else:
                v = means[a][b]
                cell = "%.2f" % v if v is not None else "none"
            out.append('<text x="%d" y="%d" font-size="11" text-anchor="middle" fill="%s">%s</text>' % (lx + 40 + (j + 1) * col, yy, INK, cell))
    y += 18 * len(SEATS) + 30
    pacts = ", ".join("%s-%s" % tuple(p) for p in state["pacts_active"]) or "none"
    out.append('<text x="%d" y="%d" font-size="11" fill="%s">pacts active: %s</text>' % (lx, y, INK, esc(pacts)))
    broken = ", ".join("%s %d" % (s, state["powers"][s]["broken_commits"]) for s in SEATS)
    betrayals = ", ".join("%s %d" % (s, state["powers"][s]["betrayals"]) for s in SEATS)
    out.append('<text x="%d" y="%d" font-size="11" fill="%s">broken commits: %s</text>' % (lx, y + 18, INK, broken))
    out.append('<text x="%d" y="%d" font-size="11" fill="%s">betrayals: %s</text>' % (lx, y + 36, INK, betrayals))
    if result:
        kinds = {}
        for e in result.get("events", []):
            kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
        summary = ", ".join("%s %d" % (k, v) for k, v in sorted(kinds.items())) or "nothing happened"
        out.append('<text x="%d" y="%d" font-size="10" fill="%s">this round: %s</text>' % (lx, y + 54, INK, esc(summary)))
        out.append('<text x="%d" y="%d" font-size="10" fill="%s">red dashes: a battle this round; grey dots: an uncontested capture</text>' % (lx, y + 72, MUTED))
    out.append('<text x="24" y="%d" font-size="10" fill="%s">circles: units inside, yield below; the large circles are homes; grey is neutral</text>' % (height - 16, MUTED))
    out.append("</svg>\n")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_new(args):
    match, _state = create_match(args.match, args.seed, args.rounds)
    print("new match %s: %d order rounds, %d move rounds, seed %r; written %s and rounds/001/state.json"
          % (match["match"], match["order_rounds"], match["rounds"], match["seed"], Path(args.match) / "match.json"))


def cmd_join(args):
    record = join_match(args.match, args.player, args.seat, args.session, args.pubkey)
    print("%s takes seat %s from round %d%s; written %s"
          % (record["player"], record["seat"], record["joined_round"],
             " with a public key" if record["pubkey"] else " (no public key: cannot receive messages)",
             Path(args.match) / "players" / (record["player"] + ".json")))


def cmd_keygen(args):
    if args.from_text is not None:
        x = secret_from_text(args.from_text)
    else:
        x = secrets.randbits(256)
    while not 1 <= x < DH_Q:
        x = secrets.randbits(256)
    path = Path(args.out)
    if path.exists():
        raise RefereeError("%s already exists; a key file is never overwritten" % path)
    write_keyfile(path, x)
    print(canonical({"pubkey": "%x" % dh_public(x), "keyfile": str(path)}), end="")


def load_orders_file(path, gmap, rules):
    path = Path(path)
    if not path.is_file():
        raise RefereeError("%s does not exist" % path)
    try:
        orders = strict_loads(path.read_text(encoding="utf-8"))
    except (ValueError, RecursionError) as e:
        raise RefereeError("%s is not valid JSON: %s" % (path, e))
    problems = check_orders(orders, gmap, rules)
    if problems:
        raise RefereeError("%s: %s" % (path, "; ".join(problems)))
    return orders


def cmd_commit(args):
    gmap, rules = None, DEFAULT_RULES
    if args.match:
        match = load_match(args.match)
        gmap, rules = match["map"], match["rules"]
    orders = load_orders_file(args.orders, gmap, rules)
    nonce = args.nonce or secrets.token_hex(16)
    if not HEX_RE.match(nonce) or not 1 <= len(nonce) <= 128:
        raise RefereeError("--nonce must be 1 to 128 lowercase hex characters")
    print(canonical({"commit": commit_hash(orders, nonce), "nonce": nonce}), end="")


def parse_stance_arg(text):
    try:
        obj = strict_loads(text)
    except (ValueError, RecursionError) as e:
        raise RefereeError("--stance must be a JSON object like '{\"name\": 0.5}': %s" % e)
    if not isinstance(obj, dict):
        raise RefereeError("--stance must be a JSON object keyed by player name")
    return obj


def write_move_file(args, move, match, state, seats):
    problems, _m = check_move(move, match, state, seats, args.player)
    if problems:
        print("the move would be rejected: %d problem(s)" % len(problems), file=sys.stderr)
        for p in problems:
            print("  %s" % p, file=sys.stderr)
        sys.exit(1)
    if args.stdout:
        sys.stdout.write(canonical(move))
        return None
    path = round_dir(args.match, state["round"]) / "moves" / ("%s.json" % args.player)
    if path.exists() and not args.force:
        raise RefereeError("%s already exists (pass --force to replace your own uncommitted move)" % path)
    write_json(path, move)
    return path


def cmd_move(args):
    match = load_match(args.match)
    round_no = parse_round(args.round)
    if round_no > match["rounds"]:
        raise RefereeError("this match has %d rounds" % match["rounds"])
    state = load_state(args.match, round_no)
    seats, _players, _problems = load_seats(args.match)
    if not NAME_RE.match(args.player or ""):
        raise RefereeError("player names are 2 to 32 lowercase letters, digits and hyphens")
    move = {"game": VERSION, "match": match["match"], "round": round_no, "player": args.player}
    committed = None
    if args.orders:
        orders = load_orders_file(args.orders, match["map"], match["rules"])
        nonce = args.nonce or secrets.token_hex(16)
        if not HEX_RE.match(nonce) or not 1 <= len(nonce) <= 128:
            raise RefereeError("--nonce must be 1 to 128 lowercase hex characters")
        move["commit"] = commit_hash(orders, nonce)
        committed = {"commit": move["commit"], "nonce": nonce}
    elif args.nonce:
        raise RefereeError("--nonce needs --orders")
    if args.prev_orders or args.prev_nonce:
        if not (args.prev_orders and args.prev_nonce):
            raise RefereeError("--prev-orders and --prev-nonce go together")
        prev = load_orders_file(args.prev_orders, match["map"], match["rules"])
        move["reveal"] = {"orders": prev, "nonce": args.prev_nonce}
    if args.stance is not None:
        move["stance"] = parse_stance_arg(args.stance)
    if args.pacts is not None:
        move["pacts"] = [p.strip() for p in args.pacts.split(",") if p.strip()]
    if args.say is not None:
        move["say"] = args.say
    path = write_move_file(args, move, match, state, seats)
    if path is not None:
        print("written %s" % path)
    if committed:
        print("committed; keep the orders file and this nonce for your reveal next round: %s" % committed["nonce"],
              file=sys.stderr if args.stdout else sys.stdout)


def cmd_bot(args):
    match = load_match(args.match)
    round_no = parse_round(args.round)
    if round_no > match["rounds"]:
        raise RefereeError("this match has %d rounds" % match["rounds"])
    state = load_state(args.match, round_no)
    if (round_dir(args.match, round_no) / "result.json").is_file():
        raise RefereeError("round %d is already resolved" % round_no)
    if not NAME_RE.match(args.player or ""):
        raise RefereeError("player names are 2 to 32 lowercase letters, digits and hyphens")
    private = Path(args.private)
    if args.nonce is not None and (not HEX_RE.match(args.nonce) or not 1 <= len(args.nonce) <= 128):
        raise RefereeError("--nonce must be 1 to 128 lowercase hex characters")
    seats, _players, _problems = load_seats(args.match)
    pending = read_sidecar(private, args.player)
    move, new_pending, notes = bot_move(state, match, seats, args.player, args.style, pending, args.nonce)
    for note in notes:
        print("  %s" % note, file=sys.stderr)
    path = write_move_file(args, move, match, state, seats)
    if new_pending is not None:
        write_json(sidecar_path(private, args.player), new_pending)
        print("  sidecar with this round's orders and nonce: %s (keep it until next round)"
              % sidecar_path(private, args.player), file=sys.stderr)
    if path is not None:
        print("written %s" % path)


def cmd_validate(args):
    match = load_match(args.match)
    round_no = parse_round(args.round)
    state = load_state(args.match, round_no)
    seats, _players, _problems = load_seats(args.match)
    path = Path(args.move)
    if not path.is_file():
        raise RefereeError("%s does not exist" % path)
    text = read_move_file(path)
    obj, problems = parse_move_text(text)
    if obj is not None:
        problems, _move = check_move(obj, match, state, seats, path.stem)
    if problems:
        print("%s: %d problem(s)" % (path, len(problems)))
        for p in problems:
            print("  %s" % p)
        sys.exit(1)
    print("%s: ok (a legal move for %s in round %d)" % (path, path.stem, round_no))


def event_summary(result):
    kinds = {}
    for e in result["events"]:
        kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
    return ", ".join("%s %d" % (k, v) for k, v in sorted(kinds.items())) or "nothing happened"


def cmd_resolve(args):
    round_no = parse_round(args.round)
    result, _next_state, differences = resolve_round(args.match, round_no, args.allow_absent, args.check)
    summary = event_summary(result)
    if args.check:
        if differences:
            print("round %03d: %d difference(s)" % (round_no, len(differences)))
            for d in differences[:40]:
                print("  %s" % d)
            sys.exit(1)
        print("round %03d: matches the committed result and next state (%s)" % (round_no, summary))
        return
    print("round %03d resolved: %s; scores %s" % (round_no, summary,
          ", ".join("%s %d" % (s, v) for s, v in sorted(result["scores"].items()))))
    if result.get("final"):
        print("final round: standings written to result.json")
        for row in result["standings"]:
            print("  %d. %s (%s) %d points, %d territories, %d units, %d resources"
                  % (row["rank"], row["player"] or "empty seat", row["seat"], row["score"],
                     row["territories"], row["units"], row["resources"]))


def cmd_verify(args):
    checked, differences = verify_match(args.match)
    for d in differences[:60]:
        print("  %s" % d)
    if differences:
        print("verify: %d round(s) recomputed, %d difference(s)" % (checked, len(differences)))
        sys.exit(1)
    print("verify: %d round(s) recomputed, all match" % checked)
    print("verify recomputes the record from the files on disk; it cannot tell whether a move was the one its player meant, nor whether a file arrived after its round was resolved.")


def latest_state(match_dir, match):
    rounds = rounds_with_state(match_dir)
    if not rounds:
        raise RefereeError("no state.json found")
    state = load_state(match_dir, rounds[-1])
    finished = latest_result_round(match_dir, match) == match["rounds"]
    return state, finished


def cmd_score(args):
    match = load_match(args.match)
    state, finished = latest_state(args.match, match)
    print("%s: after round %d of %d%s" % (match["match"], state["round"] - 1, match["rounds"],
                                          " (final)" if finished else ""))
    for row in standings(state):
        print("  %d. %s (%s) %d points, %d territories, %d units, %d resources, penalty %d"
              % (row["rank"], row["player"] or "empty seat", row["seat"], row["score"],
                 row["territories"], row["units"], row["resources"], row["penalty"]))


def cmd_ledger(args):
    match = load_match(args.match)
    state, finished = latest_state(args.match, match)
    means = inconsistency_means(state["ledger"])
    print("%s: ledger after round %d of %d%s" % (match["match"], state["round"] - 1, match["rounds"],
                                                 " (final)" if finished else ""))
    print("inconsistency: mean |stance - observed|; a row is what a seat said about the column seat (n = observations)")
    print("     " + "".join("%16s" % s for s in SEATS))
    for a in SEATS:
        cells = []
        for b in SEATS:
            if a == b:
                cells.append("%16s" % "-")
            elif means[a][b] is None:
                cells.append("%16s" % "none")
            else:
                cells.append("%16s" % ("%.3f (n=%d)" % (means[a][b], state["ledger"][a][b]["count"])))
        print("  %s  %s   %s" % (a, "".join(cells), state["seats"].get(a) or "(empty seat)"))
    print("broken commits (broken_commit and no_reveal together): "
          + ", ".join("%s %d" % (s, state["powers"][s]["broken_commits"]) for s in SEATS))
    print("betrayals: " + ", ".join("%s %d" % (s, state["powers"][s]["betrayals"]) for s in SEATS))
    print("reputation: " + ", ".join("%s %.2f" % (s, state["powers"][s]["reputation"]) for s in SEATS))
    print("pacts active: " + (", ".join("%s-%s" % tuple(p) for p in state["pacts_active"]) or "none"))


def cmd_render(args):
    match = load_match(args.match)
    if args.round is None:
        round_no = latest_result_round(args.match, match) or rounds_with_state(args.match)[-1]
    else:
        round_no = parse_round(args.round)
    result_path = round_dir(args.match, round_no) / "result.json"
    if result_path.is_file():
        result = read_json(result_path)
        state = load_state(args.match, round_no + 1)
        caption = "after round %d%s" % (round_no, " (final)" if result.get("final") else "")
    else:
        result = None
        state = load_state(args.match, round_no)
        caption = "start of round %d (unresolved)" % round_no
    sys.stdout.write(render_svg(match, state, result, caption))


def encrypt_message(match_dir, round_no, keyfile, sender, recipient, text, nonce=None):
    """Write rounds/NNN/messages/<sender>-to-<recipient>-<k>.json; return its path."""
    match_dir = Path(match_dir)
    match = load_match(match_dir)
    if round_no > match["rounds"]:
        raise RefereeError("this match has %d rounds" % match["rounds"])
    seats, players, _problems = load_seats(match_dir)
    for name in (sender, recipient):
        if name not in players:
            raise RefereeError("%r has no seat in this match" % name)
    if sender == recipient:
        raise RefereeError("a message needs two different players")
    if players[recipient]["pubkey"] is None:
        raise RefereeError("%s joined without a public key and cannot receive messages" % recipient)
    if players[sender]["pubkey"] is None:
        raise RefereeError("%s joined without a public key, so the recipient could not derive the shared secret" % sender)
    x = read_keyfile(keyfile)
    if dh_public(x) != parse_pubkey(players[sender]["pubkey"]):
        raise RefereeError("%s does not match the public key %s joined with" % (keyfile, sender))
    if len(text.encode("utf-8")) > MAX_MESSAGE_BYTES:
        raise RefereeError("a message is at most %d bytes" % MAX_MESSAGE_BYTES)
    folder = round_dir(match_dir, round_no) / "messages"
    k = 1
    while (folder / ("%s-to-%s-%d.json" % (sender, recipient, k))).exists():
        k += 1
    if nonce is None:
        nonce = secrets.token_bytes(16)
    header = {"from": sender, "to": recipient, "n": k, "match": match["match"], "round": round_no}
    msg = seal_message(x, parse_pubkey(players[recipient]["pubkey"]), header, text, nonce)
    path = folder / ("%s-to-%s-%d.json" % (sender, recipient, k))
    write_json(path, msg)
    return path


def cmd_encrypt(args):
    round_no = parse_round(args.round)
    nonce = None
    if args.nonce is not None:
        if not HEX_RE.match(args.nonce) or len(args.nonce) != 32:
            raise RefereeError("--nonce must be 32 lowercase hex characters")
        nonce = bytes.fromhex(args.nonce)
    path = encrypt_message(args.match, round_no, args.key, getattr(args, "from"), args.to, args.message, nonce)
    print("written %s (%d bytes of ciphertext)" % (path, len(read_json(path)["ciphertext"]) // 2))


def decrypt_file(keyfile, message_path, match_dir=None):
    message_path = Path(message_path)
    if not message_path.is_file():
        raise RefereeError("%s does not exist" % message_path)
    try:
        msg = strict_loads(message_path.read_text(encoding="utf-8"))
    except (ValueError, RecursionError) as e:
        raise RefereeError("%s is not valid JSON: %s" % (message_path, e))
    if not isinstance(msg, dict):
        raise RefereeError("%s is not a message file" % message_path)
    if match_dir is None:
        if len(message_path.resolve().parents) < 4:
            raise RefereeError("pass --match: the match directory cannot be inferred from this path")
        match_dir = message_path.resolve().parents[3]
    _seats, players, _problems = load_seats(match_dir)
    x = read_keyfile(keyfile)
    mine = dh_public(x)
    src, dst = msg.get("from"), msg.get("to")
    for name in (src, dst):
        if not isinstance(name, str) or name not in players or players[name]["pubkey"] is None:
            raise RefereeError("%r is not a seated player with a public key in %s" % (name, match_dir))
    if parse_pubkey(players[src]["pubkey"]) == mine:
        other = parse_pubkey(players[dst]["pubkey"])
    elif parse_pubkey(players[dst]["pubkey"]) == mine:
        other = parse_pubkey(players[src]["pubkey"])
    else:
        raise RefereeError("%s is neither %s's nor %s's key" % (keyfile, src, dst))
    return open_message(x, other, msg)


def cmd_decrypt(args):
    text = decrypt_file(args.key, args.file, args.match)
    sys.stdout.write(text + ("" if text.endswith("\n") else "\n"))


def demo_nonce(seed, round_no, player):
    return sha256_text("%s demo nonce\n%s\n%d\n%s" % (VERSION, seed, round_no, player))[:32]


DEMO_PLAYERS = [("honest-a", "a", "honest"), ("liar-b", "b", "liar"),
                ("honest-c", "c", "honest"), ("liar-d", "d", "liar")]
DEMO_MESSAGE = "The two liars both border you. I will not cross our border this match; hold the north and I hold the south."


def run_demo(match_dir, seed, order_rounds, private_dir, log=print):
    """new, four bots join (two with keys derived from the seed), every
    round moved and resolved, one encrypted message in round 2. Returns a
    summary. Everything is derived from the seed, so the demo is
    reproducible byte for byte."""
    started = time.monotonic()
    match_dir = Path(match_dir)
    private = Path(private_dir)
    private.mkdir(parents=True, exist_ok=True)
    create_match(match_dir, seed, order_rounds)
    keyfiles = {}
    for name, seat, _style in DEMO_PLAYERS:
        pubkey = None
        if name in ("honest-a", "honest-c"):
            x = secret_from_text("%s demo key\n%s\n%s" % (VERSION, seed, name))
            keyfiles[name] = private / ("%s.key.json" % name)
            if keyfiles[name].exists():
                keyfiles[name].unlink()
            write_keyfile(keyfiles[name], x)
            pubkey = "%x" % dh_public(x)
        join_match(match_dir, name, seat, None, pubkey)
    match = load_match(match_dir)
    totals = {"battle": 0, "capture": 0, "betrayal": 0, "broken_commit": 0, "no_reveal": 0, "give": 0}
    result = None
    for n in range(1, match["rounds"] + 1):
        state = load_state(match_dir, n)
        seats, _p, _q = load_seats(match_dir)
        for name, _seat, style in DEMO_PLAYERS:
            pending = read_sidecar(private, name)
            move, new_pending, notes = bot_move(state, match, seats, name, style, pending, demo_nonce(seed, n, name))
            for note in notes:
                log("  " + note)
            write_json(round_dir(match_dir, n) / "moves" / ("%s.json" % name), move)
            if new_pending is not None:
                write_json(sidecar_path(private, name), new_pending)
        if n == 2:
            nonce = bytes.fromhex(sha256_text("%s demo message nonce\n%s" % (VERSION, seed))[:32])
            encrypt_message(match_dir, n, keyfiles["honest-a"], "honest-a", "honest-c", DEMO_MESSAGE, nonce)
        result, _next, _d = resolve_round(match_dir, n)
        for e in result["events"]:
            if e["kind"] in totals:
                totals[e["kind"]] += 1
        log("round %03d: %s; scores %s" % (n, event_summary(result),
            ", ".join("%s %d" % (s, v) for s, v in sorted(result["scores"].items()))))
    final_state = load_state(match_dir, match["rounds"] + 1)
    elapsed = time.monotonic() - started
    return {"standings": standings(final_state), "ledger": final_ledger(final_state), "totals": totals,
            "seconds": elapsed, "rounds": match["rounds"]}


def cmd_demo(args):
    if args.private:
        summary = run_demo(args.match, args.seed, args.rounds, args.private)
    else:
        with tempfile.TemporaryDirectory(prefix="matrix-demo-") as private:
            summary = run_demo(args.match, args.seed, args.rounds, private)
    print("standings:")
    for row in summary["standings"]:
        print("  %d. %s (%s) %d points, %d territories, %d units, %d resources, penalty %d"
              % (row["rank"], row["player"], row["seat"], row["score"], row["territories"],
                 row["units"], row["resources"], row["penalty"]))
    means = summary["ledger"]["inconsistency"]
    print("inconsistency (row: what the seat said about the column seat):")
    print("      " + "".join("%8s" % s for s in SEATS))
    for a in SEATS:
        print("  %s   " % a + "".join("%8s" % ("-" if a == b else ("%.3f" % means[a][b] if means[a][b] is not None else "none"))
                                     for b in SEATS))
    print("betrayals: " + ", ".join("%s %d" % (s, v) for s, v in sorted(summary["ledger"]["betrayals"].items())))
    print("broken commits: " + ", ".join("%s %d" % (s, v) for s, v in sorted(summary["ledger"]["broken_commits"].items())))
    t = summary["totals"]
    print("battles %d, captures %d, betrayal events %d, gifts %d, wall time %.1f s"
          % (t["battle"], t["capture"], t["betrayal"], t["give"], summary["seconds"]))


def build_parser():
    parser = argparse.ArgumentParser(prog="matrix.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", metavar="command")
    sub.required = True

    p = sub.add_parser("new", help="create a match directory: match.json and rounds/001/state.json")
    p.add_argument("match", help="match directory (its name is the match id)")
    p.add_argument("--seed", required=True, help="text that fixes the map")
    p.add_argument("--rounds", type=int, default=DEFAULT_ORDER_ROUNDS,
                   help="order rounds (default %d); the match has one more move round" % DEFAULT_ORDER_ROUNDS)
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("join", help="take a seat: writes players/<name>.json")
    p.add_argument("match")
    p.add_argument("--player", required=True, help="your name: [a-z0-9-]{2,32}")
    p.add_argument("--seat", help="a, b, c or d (or 1-4); default: the first free seat")
    p.add_argument("--session", help="a link to your session, stored in the player file")
    p.add_argument("--pubkey", help="the hex public key keygen printed; without it you cannot receive messages")
    p.set_defaults(func=cmd_join)

    p = sub.add_parser("keygen", help="write a private key file (mode 0600) and print the public key")
    p.add_argument("--out", required=True, help="where to write the key: outside the repository")
    p.add_argument("--from-text", help="derive the secret from this text instead of the OS random source "
                                       "(demos and tests only: such a key is not secret)")
    p.set_defaults(func=cmd_keygen)

    p = sub.add_parser("commit", help="print the commit hash and nonce for an orders file")
    p.add_argument("--orders", required=True, help="JSON file with moves, recruit and give")
    p.add_argument("--nonce", help="hex nonce; default: 16 random bytes")
    p.add_argument("--match", help="match directory, to check territory ids and edges too")
    p.set_defaults(func=cmd_commit)

    p = sub.add_parser("move", help="write a complete move file: commit new orders, reveal the previous ones")
    p.add_argument("match")
    p.add_argument("round")
    p.add_argument("--player", required=True)
    p.add_argument("--orders", help="orders file to commit for the next round (not in the last round)")
    p.add_argument("--nonce", help="nonce for --orders; default: 16 random bytes, printed")
    p.add_argument("--prev-orders", help="the orders file you committed last round")
    p.add_argument("--prev-nonce", help="the nonce you used last round")
    p.add_argument("--stance", help="JSON object: trust in [0, 1] per player name")
    p.add_argument("--pacts", help="comma-separated player names you propose a pact to")
    p.add_argument("--say", help="a public note, at most 280 characters")
    p.add_argument("--stdout", action="store_true", help="print the move instead of writing it")
    p.add_argument("--force", action="store_true", help="replace an existing move file of this player")
    p.set_defaults(func=cmd_move)

    p = sub.add_parser("bot", help="write a move for a player with the reference bot")
    p.add_argument("match")
    p.add_argument("round")
    p.add_argument("--player", required=True)
    p.add_argument("--private", required=True,
                   help="directory outside the repository for the bot's sidecar (.<player>.pending.json)")
    p.add_argument("--style", default="honest", choices=list(BOT_STYLES),
                   help="honest keeps its word in stances; liar says 0.9 to everyone and attacks (default honest)")
    p.add_argument("--nonce", help="hex nonce for the commit; default: 16 random bytes")
    p.add_argument("--stdout", action="store_true", help="print the move instead of writing it (the sidecar is still written)")
    p.add_argument("--force", action="store_true", help="replace an existing move file of this player")
    p.set_defaults(func=cmd_bot)

    p = sub.add_parser("validate", help="check a move file; exit 1 and list problems if it would be rejected")
    p.add_argument("match")
    p.add_argument("round")
    p.add_argument("move", help="path to the move file (its name is the player)")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("resolve", help="play a round: writes result.json and the next state.json")
    p.add_argument("match")
    p.add_argument("round")
    p.add_argument("--allow-absent", action="store_true",
                   help="give seated players without a move file the do-nothing move")
    p.add_argument("--check", action="store_true",
                   help="recompute in memory and compare with the committed files instead of writing")
    p.set_defaults(func=cmd_resolve)

    p = sub.add_parser("verify", help="recompute every resolved round and compare with the files")
    p.add_argument("match")
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("score", help="print the standings from the latest state")
    p.add_argument("match")
    p.set_defaults(func=cmd_score)

    p = sub.add_parser("ledger", help="print the inconsistency matrix, broken commits and betrayals so far")
    p.add_argument("match")
    p.set_defaults(func=cmd_ledger)

    p = sub.add_parser("render", help="draw the map after a round as SVG on stdout (default: the latest resolved round)")
    p.add_argument("match")
    p.add_argument("round", nargs="?")
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("encrypt", help="write an encrypted message file into rounds/NNN/messages/")
    p.add_argument("match")
    p.add_argument("round")
    p.add_argument("--key", required=True, help="your key file from keygen")
    p.add_argument("--from", required=True, dest="from", help="your player name")
    p.add_argument("--to", required=True, help="the recipient's player name")
    p.add_argument("--message", required=True, help="the plaintext, at most %d bytes" % MAX_MESSAGE_BYTES)
    p.add_argument("--nonce", help="32 hex characters; default: 16 random bytes (tests and demos only)")
    p.set_defaults(func=cmd_encrypt)

    p = sub.add_parser("decrypt", help="verify a message file's MAC with your key and print the plaintext")
    p.add_argument("file", help="a file under <match>/rounds/NNN/messages/")
    p.add_argument("--key", required=True, help="your key file from keygen")
    p.add_argument("--match", help="match directory (default: inferred from the file's path)")
    p.set_defaults(func=cmd_decrypt)

    p = sub.add_parser("demo", help="new match, four bots join, every round is moved and resolved")
    p.add_argument("match", help="directory to create, e.g. games/matrix/000-demo")
    p.add_argument("--seed", required=True)
    p.add_argument("--rounds", type=int, default=DEFAULT_ORDER_ROUNDS, help="order rounds (default %d)" % DEFAULT_ORDER_ROUNDS)
    p.add_argument("--private", help="directory for the bots' sidecars and the demo keys (default: a temporary one)")
    p.set_defaults(func=cmd_demo)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except RefereeError as e:
        print("matrix: %s" % e, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

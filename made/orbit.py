#!/usr/bin/env python3
"""Orbit: the League's orbital-mechanics referee (version string orbit/1).

A planar world: a planet (mu = 1) with one moon, six stations on circular
orbits, four seats of three craft each, and debris that multiplies when
anything is destroyed. Players capture stations by rendezvous, hold them
to score, and may fire slugs at rival craft. Rules: made/orbit.md.
Shared protocol: made/league.md.

Usage (from the repository root):

  python3 made/orbit.py new      games/orbit/001-first-light --seed first-light [--rounds 10]
  python3 made/orbit.py join     games/orbit/001-first-light --player <name> [--seat a|b|c|d] [--session <link>]
  python3 made/orbit.py bot      games/orbit/001-first-light <round> --player <name> [--style greedy|hawk]
  python3 made/orbit.py validate games/orbit/001-first-light <round> <move-file>
  python3 made/orbit.py resolve  games/orbit/001-first-light <round> [--allow-absent] [--check]
  python3 made/orbit.py verify   games/orbit/001-first-light
  python3 made/orbit.py score    games/orbit/001-first-light
  python3 made/orbit.py render   games/orbit/001-first-light [<round>] > picture.svg
  python3 made/orbit.py plan     games/orbit/001-first-light <round> --craft a1 --target n3 [--fuel-cap 0.4]
  python3 made/orbit.py demo     games/orbit/000-demo --seed first-light [--rounds 10]

Standard library only. The simulation is a set of pure functions over plain
dicts (simulate_round and what it calls); the command-line layer only reads
and writes files.
"""
import argparse
import hashlib
import json
import math
import random
import re
import sys
from pathlib import Path

VERSION = "orbit/1"
NAME_RE = re.compile(r"^[a-z0-9-]{2,32}$")
SEATS = ["a", "b", "c", "d"]
CRAFT_PER_SEAT = 3
NODE_IDS = ["n1", "n2", "n3", "n4", "n5", "n6"]
TRACE_EVERY = 50          # integration steps between trace samples
MAX_MOVE_BYTES = 65536    # a move file larger than this is rejected unread
MAX_LIST = 64             # longest list or object a move file may contain

DEFAULT_RULES = {
    "mu": 1.0,
    "r_min": 1.0,
    "r_max": 24.0,
    "mu_moon": 0.012,
    "r_moon": 14.0,
    "moon_radius": 0.3,
    "node_radii": [3.0, 4.0, 5.0, 6.5, 8.0, 10.0],
    "r_park": 2.0,
    "fuel": 2.0,
    "slugs": 2,
    "debris_initial": 8,
    "debris_per_round": 1,
    "debris_periapsis": [2.5, 11.0],
    "debris_eccentricity": [0.0, 0.3],
    "T": 20.0,
    "dt": 0.02,
    "max_burns": 4,
    "slug_speed": 0.3,
    "hit_radius": 0.05,
    "capture_radius": 0.15,
    "capture_speed": 0.05,
    "node_point": 1,
    "kill_point": 3,
}


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
    except (TypeError, ValueError):
        return text


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical(rounded(obj)), encoding="utf-8")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def norm(v):
    return math.sqrt(v[0] * v[0] + v[1] * v[1])


# ---------------------------------------------------------------------------
# The world: analytic bodies and the gravity field
# ---------------------------------------------------------------------------

def node_rate(r, rules):
    return math.sqrt(rules["mu"] / (r * r * r))


def moon_rate(rules):
    r = rules["r_moon"]
    return math.sqrt((1.0 + rules["mu_moon"]) / (r * r * r))


def circular_state(r, angle, n):
    """Position and velocity on a prograde circular orbit of radius r."""
    c, s = math.cos(angle), math.sin(angle)
    return [r * c, r * s], [-r * n * s, r * n * c]


def node_state(node, t, rules):
    n = node_rate(node["r"], rules)
    return circular_state(node["r"], node["phase"] + n * t, n)


def moon_position(phase, t, rules):
    a = phase + moon_rate(rules) * t
    return rules["r_moon"] * math.cos(a), rules["r_moon"] * math.sin(a)


def orbit_state(rp, e, argp, nu, mu):
    """Position and velocity from periapsis radius, eccentricity, argument
    of periapsis and true anomaly, prograde."""
    p = rp * (1.0 + e)
    r = p / (1.0 + e * math.cos(nu))
    theta = argp + nu
    pos = [r * math.cos(theta), r * math.sin(theta)]
    v = math.sqrt(mu / p)
    vr, vt = v * e * math.sin(nu), v * (1.0 + e * math.cos(nu))
    c, s = math.cos(theta), math.sin(theta)
    return pos, [vr * c - vt * s, vr * s + vt * c]


def draw_debris(rng, rules):
    lo, hi = rules["debris_periapsis"]
    elo, ehi = rules["debris_eccentricity"]
    rp = rng.uniform(lo, hi)
    e = rng.uniform(elo, ehi)
    argp = rng.uniform(0.0, 2.0 * math.pi)
    nu = rng.uniform(0.0, 2.0 * math.pi)
    pos, vel = orbit_state(rp, e, argp, nu, rules["mu"])
    return {"pos": pos, "vel": vel}


def step_body(x, y, vx, vy, dt, mu, mum, m0, mh, m1):
    """One RK4 step of a point mass in the planet + moon field.

    m0, mh, m1 are the moon's positions at the start, middle and end of the
    step. Raises ZeroDivisionError if a stage lands exactly on a centre."""
    # stage 1
    r2 = x * x + y * y
    f = -mu / (r2 * math.sqrt(r2))
    ax1, ay1 = f * x, f * y
    if mum:
        dx, dy = x - m0[0], y - m0[1]
        d2 = dx * dx + dy * dy
        g = -mum / (d2 * math.sqrt(d2))
        ax1 += g * dx
        ay1 += g * dy
    # stage 2
    h = 0.5 * dt
    x2, y2 = x + h * vx, y + h * vy
    vx2, vy2 = vx + h * ax1, vy + h * ay1
    r2 = x2 * x2 + y2 * y2
    f = -mu / (r2 * math.sqrt(r2))
    ax2, ay2 = f * x2, f * y2
    if mum:
        dx, dy = x2 - mh[0], y2 - mh[1]
        d2 = dx * dx + dy * dy
        g = -mum / (d2 * math.sqrt(d2))
        ax2 += g * dx
        ay2 += g * dy
    # stage 3
    x3, y3 = x + h * vx2, y + h * vy2
    vx3, vy3 = vx + h * ax2, vy + h * ay2
    r2 = x3 * x3 + y3 * y3
    f = -mu / (r2 * math.sqrt(r2))
    ax3, ay3 = f * x3, f * y3
    if mum:
        dx, dy = x3 - mh[0], y3 - mh[1]
        d2 = dx * dx + dy * dy
        g = -mum / (d2 * math.sqrt(d2))
        ax3 += g * dx
        ay3 += g * dy
    # stage 4
    x4, y4 = x + dt * vx3, y + dt * vy3
    vx4, vy4 = vx + dt * ax3, vy + dt * ay3
    r2 = x4 * x4 + y4 * y4
    f = -mu / (r2 * math.sqrt(r2))
    ax4, ay4 = f * x4, f * y4
    if mum:
        dx, dy = x4 - m1[0], y4 - m1[1]
        d2 = dx * dx + dy * dy
        g = -mum / (d2 * math.sqrt(d2))
        ax4 += g * dx
        ay4 += g * dy
    s = dt / 6.0
    return (x + s * (vx + 2.0 * vx2 + 2.0 * vx3 + vx4),
            y + s * (vy + 2.0 * vy2 + 2.0 * vy3 + vy4),
            vx + s * (ax1 + 2.0 * ax2 + 2.0 * ax3 + ax4),
            vy + s * (ay1 + 2.0 * ay2 + 2.0 * ay3 + ay4))


def moon_triplet(phase, t, dt, rules):
    return (moon_position(phase, t, rules),
            moon_position(phase, t + 0.5 * dt, rules),
            moon_position(phase, t + dt, rules))


def body_fate(x, y, moon, rules):
    """None, or the event kind that removes a body at this position."""
    r2 = x * x + y * y
    if r2 < rules["r_min"] ** 2:
        return "reentry"
    if r2 > rules["r_max"] ** 2:
        return "escaped"
    dx, dy = x - moon[0], y - moon[1]
    if dx * dx + dy * dy < rules["moon_radius"] ** 2:
        return "moon_impact"
    return None


def propagate(pos, vel, t0, steps, dt, rules, moon_phase, burns=None):
    """Integrate one unpowered body (plus optional impulsive burns, a dict
    step index -> [dvx, dvy]) and return the list of (x, y, vx, vy) at every
    step boundary, index 0 being the start. Stops early (shorter list) if
    the body re-enters, escapes or hits the moon. Same arithmetic as the
    referee, so with the referee's dt the trajectory is the referee's."""
    mu, mum = rules["mu"], rules["mu_moon"]
    x, y = pos
    vx, vy = vel
    out = [(x, y, vx, vy)]
    for k in range(steps):
        t = t0 + k * dt
        if burns and k in burns:
            vx += burns[k][0]
            vy += burns[k][1]
            out[-1] = (x, y, vx, vy)
        m0, mh, m1 = moon_triplet(moon_phase, t, dt, rules)
        try:
            x, y, vx, vy = step_body(x, y, vx, vy, dt, mu, mum, m0, mh, m1)
        except (ZeroDivisionError, OverflowError):
            break
        if body_fate(x, y, m1, rules):
            break
        out.append((x, y, vx, vy))
    return out


def step_index(t, dt):
    """The step whose start time is the closest multiple of dt not above t."""
    return int(math.floor(t / dt + 1e-9))


# ---------------------------------------------------------------------------
# Making a world
# ---------------------------------------------------------------------------

def new_match(match_id, seed, rounds, rules=None):
    """match.json and the round-1 state for a fresh match."""
    rules = dict(DEFAULT_RULES if rules is None else rules)
    match = {"game": VERSION, "match": match_id, "seed": seed, "rounds": rounds,
             "seats": list(SEATS), "rules": rules}
    rng = seeded_rng(VERSION + "\n" + seed)
    moon_phase = rng.uniform(0.0, 2.0 * math.pi)
    nodes = {}
    for nid, r in zip(NODE_IDS, rules["node_radii"]):
        nodes[nid] = {"r": float(r), "phase": rng.uniform(0.0, 2.0 * math.pi), "owner": None}
    craft = {}
    n_park = node_rate(rules["r_park"], rules)
    for k, seat in enumerate(SEATS):
        for j in range(CRAFT_PER_SEAT):
            angle = math.radians(k * 90.0 + (j - 1) * 6.0)
            pos, vel = circular_state(rules["r_park"], angle, n_park)
            craft[f"{seat}{j + 1}"] = {"seat": seat, "pos": pos, "vel": vel,
                                       "fuel": float(rules["fuel"]), "slugs": int(rules["slugs"]),
                                       "alive": True}
    debris = {}
    for i in range(rules["debris_initial"]):
        debris[f"x{i + 1}"] = draw_debris(rng, rules)
    state = {"game": VERSION, "match": match_id, "round": 1, "t": 0.0,
             "seats": {s: None for s in SEATS}, "moon": {"phase": moon_phase},
             "nodes": nodes, "craft": craft, "debris": debris, "slugs": {},
             "next_debris": rules["debris_initial"] + 1, "next_slug": 1,
             "scores": {}, "kills": {}, "captures": {}}
    return match, state


# ---------------------------------------------------------------------------
# Reading a move file without trusting it
# ---------------------------------------------------------------------------

def strict_loads(text):
    """json.loads that rejects duplicate keys and NaN/Infinity."""
    def pairs_hook(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                raise ValueError(f"duplicate key {key!r}")
            out[key] = value
        return out

    def bad_constant(name):
        raise ValueError(f"{name} is not a number this game accepts")

    return json.loads(text, object_pairs_hook=pairs_hook, parse_constant=bad_constant)


def is_number(x):
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return False
    try:
        return math.isfinite(x)
    except OverflowError:
        return False


def parse_move_text(text):
    """(object or None, problems) for the raw text of a move file."""
    if len(text.encode("utf-8")) > MAX_MOVE_BYTES:
        return None, [f"move file is larger than {MAX_MOVE_BYTES} bytes"]
    try:
        obj = strict_loads(text)
    except (ValueError, RecursionError) as e:
        return None, [f"not valid JSON: {e}"]
    return obj, []


def _vector(v, what):
    if not isinstance(v, list) or len(v) != 2 or not all(is_number(c) for c in v):
        return None, [f"{what} must be a list of two finite numbers"]
    return [float(v[0]), float(v[1])], []


def _impulse(entry, what, T):
    """Validate {"t": .., "dv": [..]}; return ((t, dv), problems)."""
    problems = []
    if not isinstance(entry, dict):
        return None, [f"{what} must be an object with t and dv"]
    extra = sorted(set(entry) - {"t", "dv"})
    if extra:
        problems.append(f"{what} has unknown keys {extra}")
    t = entry.get("t")
    if not is_number(t):
        problems.append(f"{what}: t must be a finite number")
    elif not 0.0 <= t < T:
        problems.append(f"{what}: t must satisfy 0 <= t < {T}")
    dv, dv_problems = _vector(entry.get("dv"), f"{what}: dv")
    problems += dv_problems
    if problems:
        return None, problems
    return (float(t), dv), []


def check_move(obj, match, state, seats, player):
    """Validate a parsed move against the match, the round's state and the
    seat map. Returns (problems, plan); plan is craft id -> {"burns": [(t,
    dv), ...], "fire": (t, dv) or None} and is empty unless problems is."""
    rules = match["rules"]
    T = rules["T"]
    problems = []
    if not isinstance(obj, dict):
        return ["move must be a JSON object"], {}
    if not isinstance(player, str) or not NAME_RE.match(player):
        problems.append("player name must match ^[a-z0-9-]{2,32}$")
    extra = sorted(set(obj) - {"game", "match", "round", "player", "craft"})
    if extra:
        problems.append(f"unknown top-level keys {extra}")
    for key in ("game", "match", "round", "player", "craft"):
        if key not in obj:
            problems.append(f"missing field {key!r}")
    if problems:
        return problems, {}
    if obj["game"] != VERSION:
        problems.append(f"game must be {VERSION!r}")
    if obj["match"] != match["match"]:
        problems.append(f"match must be {match['match']!r}")
    if isinstance(obj["round"], bool) or not isinstance(obj["round"], int) or obj["round"] != state["round"]:
        problems.append(f"round must be the integer {state['round']}")
    if obj["player"] != player:
        problems.append(f"player must be {player!r} (the file name)")
    seat = None
    for s, name in seats.items():
        if name == player:
            seat = s
    if seat is None:
        problems.append(f"{player!r} has no seat in this match")
    craft = obj["craft"]
    if not isinstance(craft, dict):
        problems.append("craft must be an object keyed by craft id")
    elif len(craft) > MAX_LIST:
        problems.append(f"craft names more than {MAX_LIST} entries")
    if problems:
        return problems, {}
    plan = {}
    for cid in sorted(craft):
        entry = craft[cid]
        here = state["craft"].get(cid) if isinstance(cid, str) else None
        if here is None:
            problems.append(f"{cid!r} is not a craft id")
            continue
        if here["seat"] != seat:
            problems.append(f"{cid} belongs to seat {here['seat']}, not to {player}")
            continue
        if not here["alive"]:
            problems.append(f"{cid} is destroyed")
            continue
        if not isinstance(entry, dict):
            problems.append(f"{cid}: entry must be an object")
            continue
        extra = sorted(set(entry) - {"burns", "fire"})
        if extra:
            problems.append(f"{cid}: unknown keys {extra}")
        burns = entry.get("burns", [])
        parsed_burns = []
        if not isinstance(burns, list):
            problems.append(f"{cid}: burns must be a list")
        elif len(burns) > rules["max_burns"]:
            problems.append(f"{cid}: at most {rules['max_burns']} burns per round")
        else:
            total = 0.0
            for i, b in enumerate(burns):
                imp, imp_problems = _impulse(b, f"{cid}: burn {i}", T)
                problems += imp_problems
                if imp is None:
                    continue
                mag = norm(imp[1])
                if mag > here["fuel"] + 1e-9:
                    problems.append(f"{cid}: burn {i} needs {mag:.6f} dv, fuel is {here['fuel']:.6f}")
                total += mag
                parsed_burns.append(imp)
            if total > here["fuel"] + 1e-9:
                problems.append(f"{cid}: burns total {total:.6f} dv, fuel is {here['fuel']:.6f}")
        fire = entry.get("fire")
        parsed_fire = None
        if fire is not None:
            imp, imp_problems = _impulse(fire, f"{cid}: fire", T)
            problems += imp_problems
            if imp is not None:
                if norm(imp[1]) > rules["slug_speed"] + 1e-9:
                    problems.append(f"{cid}: fire dv must not exceed {rules['slug_speed']}")
                if here["slugs"] < 1:
                    problems.append(f"{cid} has no slugs left")
                parsed_fire = imp
        plan[cid] = {"burns": parsed_burns, "fire": parsed_fire}
    if problems:
        return problems, {}
    return [], plan


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
            problems.append(f"players/{stem}.json: not a player file")
            continue
        if obj.get("player") != stem or obj.get("seat") not in SEATS or obj.get("game") != VERSION:
            problems.append(f"players/{stem}.json: name, seat or game does not match")
            continue
        joined = obj.get("joined_round")
        if isinstance(joined, bool) or not isinstance(joined, int):
            joined = 0
        claims.append((joined, stem, obj["seat"], obj))
    for joined, stem, seat, obj in sorted(claims, key=lambda c: (c[0], c[1])):
        if seats[seat] is not None:
            problems.append(f"players/{stem}.json: seat {seat} already taken by {seats[seat]}")
            continue
        seats[seat] = stem
        players[stem] = {"seat": seat, "joined_round": joined, "session": obj.get("session")}
    return seats, players, problems


# ---------------------------------------------------------------------------
# Resolving a round: the whole game, as one pure function
# ---------------------------------------------------------------------------

def _copy(obj):
    return json.loads(json.dumps(obj))


def simulate_round(state, rules, seats, plans, rng):
    """Play one round. state: the round's starting state; seats: seat ->
    player or None; plans: player -> validated plan (see check_move); rng:
    the round's random.Random. Returns (next_state, outcome), where outcome
    holds events, scores_delta, scores, kills, kills_delta, captures and
    traces. Nothing here touches the filesystem or the clock."""
    T, dt = rules["T"], rules["dt"]
    steps = int(round(T / dt))
    t0 = state["t"]
    moon_phase = state["moon"]["phase"]
    mu, mum = rules["mu"], rules["mu_moon"]
    nodes = _copy(state["nodes"])
    craft = _copy(state["craft"])
    debris = _copy(state["debris"])
    slugs = _copy(state.get("slugs", {}))
    next_debris = state["next_debris"]
    next_slug = state.get("next_slug", 1)
    scores = dict(state["scores"])
    kills = dict(state["kills"])
    captures = dict(state["captures"])
    for name in seats.values():
        if name is not None:
            scores.setdefault(name, 0)
            kills.setdefault(name, 0)
            captures.setdefault(name, 0)
    scores_delta = {name: 0 for name in scores}
    kills_delta = {name: 0 for name in scores}
    events = []

    for _ in range(rules["debris_per_round"]):
        did = f"x{next_debris}"
        next_debris += 1
        debris[did] = draw_debris(rng, rules)
        events.append({"t": t0, "kind": "debris_spawn", "id": did, "source": "round"})

    burns_at, fires_at = {}, {}
    for player in sorted(plans):
        for cid in sorted(plans[player]):
            entry = plans[player][cid]
            for t, dv in entry["burns"]:
                burns_at.setdefault(step_index(t, dt), []).append((cid, dv))
            if entry["fire"] is not None:
                t, dv = entry["fire"]
                fires_at.setdefault(step_index(t, dt), []).append((cid, dv))

    traces = {}

    def sample(k):
        t = t0 + k * dt
        for cid, c in craft.items():
            if c["alive"]:
                traces.setdefault(cid, []).append(list(c["pos"]))
        for did, d in debris.items():
            traces.setdefault(did, []).append(list(d["pos"]))
        for sid, s in slugs.items():
            traces.setdefault(sid, []).append(list(s["pos"]))
        for nid, nd in nodes.items():
            traces.setdefault(nid, []).append(node_state(nd, t, rules)[0])
        traces.setdefault("moon", []).append(list(moon_position(moon_phase, t, rules)))

    sample(0)
    hr2 = rules["hit_radius"] ** 2
    for k in range(steps):
        t = t0 + k * dt
        for cid, dv in burns_at.get(k, ()):
            c = craft[cid]
            mag = norm(dv)
            if not c["alive"] or mag > c["fuel"] + 1e-9:
                continue
            c["vel"] = [c["vel"][0] + dv[0], c["vel"][1] + dv[1]]
            c["fuel"] = max(0.0, c["fuel"] - mag)
            events.append({"t": t, "kind": "burn", "id": cid, "player": seats[c["seat"]],
                           "dv": list(dv), "fuel": c["fuel"]})
        for cid, dv in fires_at.get(k, ()):
            c = craft[cid]
            if not c["alive"] or c["slugs"] < 1:
                continue
            sid = f"s{next_slug}"
            next_slug += 1
            c["slugs"] -= 1
            slugs[sid] = {"owner": seats[c["seat"]], "pos": list(c["pos"]),
                          "vel": [c["vel"][0] + dv[0], c["vel"][1] + dv[1]]}
            events.append({"t": t, "kind": "fire", "id": cid, "player": seats[c["seat"]],
                           "slug": sid, "dv": list(dv)})
        m0, mh, m1 = moon_triplet(moon_phase, t, dt, rules)
        t1 = t0 + (k + 1) * dt
        for group in (craft, debris, slugs):
            for bid in sorted(group):
                b = group[bid]
                if group is craft and not b["alive"]:
                    continue
                try:
                    x, y, vx, vy = step_body(b["pos"][0], b["pos"][1], b["vel"][0], b["vel"][1],
                                             dt, mu, mum, m0, mh, m1)
                except (ZeroDivisionError, OverflowError):
                    x, y, vx, vy = 0.0, 0.0, 0.0, 0.0
                b["pos"] = [x, y]
                b["vel"] = [vx, vy]
        for cid in sorted(craft):
            c = craft[cid]
            if c["alive"]:
                fate = body_fate(c["pos"][0], c["pos"][1], m1, rules)
                if fate:
                    c["alive"] = False
                    events.append({"t": t1, "kind": fate, "id": cid, "player": seats[c["seat"]]})
        for group in (debris, slugs):
            for bid in sorted(group):
                b = group[bid]
                fate = body_fate(b["pos"][0], b["pos"][1], m1, rules)
                if fate:
                    del group[bid]
                    events.append({"t": t1, "kind": fate, "id": bid})
        for cid in sorted(craft):
            c = craft[cid]
            if not c["alive"]:
                continue
            owner = seats[c["seat"]]
            x, y = c["pos"]
            hit_by = None
            for did in sorted(debris):
                p = debris[did]["pos"]
                dx, dy = p[0] - x, p[1] - y
                if dx * dx + dy * dy < hr2:
                    hit_by = did
                    break
            if hit_by is None:
                for sid in sorted(slugs):
                    s = slugs[sid]
                    if owner is not None and s["owner"] == owner:
                        continue
                    p = s["pos"]
                    dx, dy = p[0] - x, p[1] - y
                    if dx * dx + dy * dy < hr2:
                        hit_by = sid
                        break
            if hit_by is None:
                continue
            c["alive"] = False
            shooter = None
            if hit_by in slugs:
                shooter = slugs.pop(hit_by)["owner"]
            wid = f"x{next_debris}"
            next_debris += 1
            debris[wid] = {"pos": list(c["pos"]), "vel": list(c["vel"])}
            points = 0
            if shooter is not None and owner is not None and shooter != owner:
                points = rules["kill_point"]
                kills[shooter] = kills.get(shooter, 0) + 1
                kills_delta[shooter] = kills_delta.get(shooter, 0) + 1
                scores_delta[shooter] = scores_delta.get(shooter, 0) + points
            events.append({"t": t1, "kind": "hit", "id": cid, "player": owner, "by": hit_by,
                           "shooter": shooter, "points": points, "debris": wid})
        if (k + 1) % TRACE_EVERY == 0:
            sample(k + 1)

    t_end = t0 + steps * dt
    for sid in sorted(slugs):
        wid = f"x{next_debris}"
        next_debris += 1
        debris[wid] = {"pos": list(slugs[sid]["pos"]), "vel": list(slugs[sid]["vel"])}
        events.append({"t": t_end, "kind": "debris_spawn", "id": wid, "source": "slug", "from": sid})
    slugs = {}

    for nid in sorted(nodes):
        nd = nodes[nid]
        npos, nvel = node_state(nd, t_end, rules)
        best = None
        for cid in sorted(craft):
            c = craft[cid]
            player = seats[c["seat"]]
            if not c["alive"] or player is None:
                continue
            dist = math.hypot(c["pos"][0] - npos[0], c["pos"][1] - npos[1])
            if dist >= rules["capture_radius"]:
                continue
            speed = math.hypot(c["vel"][0] - nvel[0], c["vel"][1] - nvel[1])
            if speed >= rules["capture_speed"]:
                continue
            if best is None or dist < best[0]:
                best = (dist, cid, player, speed)
        if best is not None and nd["owner"] != best[2]:
            events.append({"t": t_end, "kind": "capture", "node": nid, "id": best[1],
                           "player": best[2], "from": nd["owner"],
                           "distance": best[0], "speed": best[3]})
            nd["owner"] = best[2]
            captures[best[2]] = captures.get(best[2], 0) + 1

    for nid in sorted(nodes):
        owner = nodes[nid]["owner"]
        if owner is not None:
            scores_delta[owner] = scores_delta.get(owner, 0) + rules["node_point"]
    for name, delta in scores_delta.items():
        scores[name] = scores.get(name, 0) + delta

    next_state = {"game": state["game"], "match": state["match"], "round": state["round"] + 1,
                  "t": t_end, "seats": dict(seats), "moon": {"phase": moon_phase},
                  "nodes": nodes, "craft": craft, "debris": debris, "slugs": slugs,
                  "next_debris": next_debris, "next_slug": next_slug,
                  "scores": scores, "kills": kills, "captures": captures}
    outcome = {"events": events, "scores_delta": scores_delta, "scores": scores,
               "kills": kills, "kills_delta": kills_delta, "captures": captures,
               "traces": traces}
    return next_state, outcome


def standings(state):
    """Players ordered by score, then kills, then name; equal (score, kills)
    share a rank."""
    rows = []
    seat_of = {name: seat for seat, name in state["seats"].items() if name}
    for name in sorted(state["scores"]):
        rows.append({"player": name, "seat": seat_of.get(name),
                     "score": state["scores"][name], "kills": state["kills"].get(name, 0),
                     "nodes": sum(1 for n in state["nodes"].values() if n["owner"] == name)})
    rows.sort(key=lambda r: (-r["score"], -r["kills"], r["player"]))
    rank = 0
    for i, row in enumerate(rows):
        if i == 0 or (row["score"], row["kills"]) != (rows[i - 1]["score"], rows[i - 1]["kills"]):
            rank = i + 1
        row["rank"] = rank
    return rows


# ---------------------------------------------------------------------------
# Files: the match directory
# ---------------------------------------------------------------------------

class RefereeError(Exception):
    """Something the command line reports and exits 1 on."""


def round_dir(match_dir, round_no):
    return Path(match_dir) / "rounds" / f"{round_no:03d}"


def parse_round(text):
    try:
        n = int(str(text), 10)
    except ValueError:
        raise RefereeError(f"round must be a number, not {text!r}")
    if n < 1 or n > 999:
        raise RefereeError("round must be between 1 and 999")
    return n


def load_match(match_dir):
    path = Path(match_dir) / "match.json"
    if not path.is_file():
        raise RefereeError(f"{path} does not exist; is this a match directory?")
    try:
        match = read_json(path)
    except ValueError as e:
        raise RefereeError(f"{path} is not valid JSON: {e}")
    if not isinstance(match, dict) or match.get("game") != VERSION:
        raise RefereeError(f"{path} is not an {VERSION} match")
    for key in ("match", "seed", "rounds", "rules"):
        if key not in match:
            raise RefereeError(f"{path} lacks {key!r}")
    return match


def load_state(match_dir, round_no):
    path = round_dir(match_dir, round_no) / "state.json"
    if not path.is_file():
        raise RefereeError(f"{path} does not exist")
    state = read_json(path)
    if state.get("round") != round_no:
        raise RefereeError(f"{path} says round {state.get('round')}, not {round_no}")
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


def read_move_file(path):
    """Raw text of a move file, read as bytes and decoded leniently, cut
    off a little past the size cap so an enormous file is not read whole."""
    with open(path, "rb") as fh:
        data = fh.read(MAX_MOVE_BYTES + 1)
    return data.decode("utf-8", errors="replace")


def read_moves(match_dir, round_no, match, state, seats):
    """Every move file for the round: (moved, invalid, plans, seed_texts)."""
    folder = round_dir(match_dir, round_no) / "moves"
    moved, invalid, plans, seed_texts = [], {}, {}, []
    if folder.is_dir():
        for p in sorted(folder.glob("*.json")):
            if not p.is_file():
                continue
            text = read_move_file(p)
            seed_texts.append((p.stem, move_text_for_seed(text)))
            obj, problems = parse_move_text(text)
            if obj is not None:
                problems, plan = check_move(obj, match, state, seats, p.stem)
            if problems:
                invalid[p.stem] = problems
            else:
                plans[p.stem] = plan
                moved.append(p.stem)
    return moved, invalid, plans, seed_texts


def compare(a, b, path="", tol=1e-8):
    """Differences between two JSON values: numbers within tol, all else exact."""
    if isinstance(a, bool) or isinstance(b, bool) or a is None or b is None or isinstance(a, str) or isinstance(b, str):
        return [] if a == b else [f"{path or '/'}: {a!r} != {b!r}"]
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if isinstance(a, int) and isinstance(b, int):
            return [] if a == b else [f"{path or '/'}: {a} != {b}"]
        return [] if abs(a - b) <= tol else [f"{path or '/'}: {a!r} differs from {b!r} by more than {tol}"]
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for key in sorted(set(a) | set(b)):
            if key not in a or key not in b:
                out.append(f"{path}/{key}: present on one side only")
            else:
                out += compare(a[key], b[key], f"{path}/{key}", tol)
        return out
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return [f"{path or '/'}: lists of length {len(a)} and {len(b)}"]
        out = []
        for i, (x, y) in enumerate(zip(a, b)):
            out += compare(x, y, f"{path}[{i}]", tol)
        return out
    return [f"{path or '/'}: {type(a).__name__} vs {type(b).__name__}"]


def resolve_round(match_dir, round_no, allow_absent=False, check=False):
    """Resolve one round from its files. Writes result.json and the next
    state.json, or with check=True recomputes them in memory and returns
    the list of differences from the committed files. Returns (result,
    next_state, differences)."""
    match_dir = Path(match_dir)
    match = load_match(match_dir)
    if round_no > match["rounds"]:
        raise RefereeError(f"this match has {match['rounds']} rounds")
    state = load_state(match_dir, round_no)
    here = round_dir(match_dir, round_no)
    result_path = here / "result.json"
    next_path = round_dir(match_dir, round_no + 1) / "state.json"
    if check and not result_path.is_file():
        raise RefereeError(f"{result_path} does not exist, nothing to check")
    if not check and result_path.is_file():
        raise RefereeError(f"{result_path} already exists; a result is never overwritten "
                           "(use --check to recompute and compare)")
    seats, players, seat_problems = load_seats(match_dir)
    seated = sorted(name for name in seats.values() if name)
    if not seated:
        raise RefereeError("no player has joined this match; there is nothing to resolve")
    moved, invalid, plans, seed_texts = read_moves(match_dir, round_no, match, state, seats)
    absent = [name for name in seated if name not in moved and name not in invalid]
    if absent and not (allow_absent or check):
        raise RefereeError("no move file for: " + ", ".join(absent) +
                           " (pass --allow-absent to give them the do-nothing move)")
    seed = round_seed(match["seed"], round_no, seed_texts)
    rng = random.Random(int(seed, 16))
    next_state, outcome = simulate_round(state, match["rules"], seats, plans, rng)
    next_state = rounded(next_state)
    next_text = canonical(next_state)
    result = {"game": VERSION, "match": match["match"], "round": round_no, "seed": seed,
              "seats": seats, "moved": moved, "absent": absent, "invalid": invalid,
              "player_file_problems": seat_problems}
    result.update(outcome)
    result["next_state_sha256"] = sha256_text(next_text)
    if round_no >= match["rounds"]:
        result["final"] = True
        result["standings"] = standings(next_state)
    result = rounded(result)
    differences = []
    if check:
        committed = read_json(result_path)
        differences += [f"result.json{d}" for d in compare(committed, result)]
        if next_path.is_file():
            differences += [f"next state.json{d}" for d in compare(read_json(next_path), next_state)]
        else:
            differences.append(f"{next_path} is missing")
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
        differences += [f"round {n:03d}: {d}" for d in diffs]
    return checked, differences


def create_match(match_dir, seed, rounds):
    match_dir = Path(match_dir)
    if (match_dir / "match.json").exists():
        raise RefereeError(f"{match_dir / 'match.json'} already exists; a match is never recreated")
    match_id = match_dir.name
    if not match_id or not re.match(r"^[A-Za-z0-9._-]+$", match_id):
        raise RefereeError("the match directory's name is the match id: letters, digits, . _ - only")
    if rounds < 1 or rounds > 999:
        raise RefereeError("rounds must be between 1 and 999")
    match, state = new_match(match_id, seed, rounds)
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


def join_match(match_dir, name, seat=None, session=None):
    match_dir = Path(match_dir)
    match = load_match(match_dir)
    if not isinstance(name, str) or not NAME_RE.match(name):
        raise RefereeError("player names are 2 to 32 lowercase letters, digits and hyphens")
    path = match_dir / "players" / f"{name}.json"
    if path.exists():
        raise RefereeError(f"{path} already exists; player files are never rewritten")
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
        raise RefereeError(f"seat {wanted} is taken by {seats[wanted]}")
    record = {"game": VERSION, "match": match["match"], "player": name, "seat": wanted,
              "session": session, "joined_round": round_no}
    write_json(path, record)
    return record


# ---------------------------------------------------------------------------
# The reference bot
# ---------------------------------------------------------------------------

SEARCH_DT = 0.2          # integration step for the first, coarse grid search
REFINE_DT = 0.1          # step for refining the best grid candidate
GRID_DIRECTIONS = 24     # first-burn directions tried (relative to the velocity)
GRID_MAGNITUDES = 6      # first-burn magnitudes tried, from 0.02 to the fuel cap
FUEL_CAP = 0.4           # largest first burn the bot considers
HOLD_BURN_CAP = 0.08     # station-keeping burns above this are not worth it
COMMIT_DISTANCE = 1.0    # a transfer ending further than this from its node waits
HAWK_RANGE = 2.0         # hawk considers rivals that come this close
HAWK_MISS = 0.03         # hawk fires only if the predicted miss is under this
MAX_CANDIDATES = 8       # grid candidates carried into the two-burn stage


def precomputed_moons(moon_phase, t0, steps, dt, rules):
    return [moon_triplet(moon_phase, t0 + k * dt, dt, rules) for k in range(steps)]


def propagate_fast(pos, vel, t0, steps, dt, rules, moon_phase, burns, moons):
    """propagate() with the moon positions supplied, for the bot's loops."""
    mu, mum = rules["mu"], rules["mu_moon"]
    x, y = pos
    vx, vy = vel
    out = [(x, y, vx, vy)]
    for k in range(steps):
        if burns and k in burns:
            vx += burns[k][0]
            vy += burns[k][1]
            out[-1] = (x, y, vx, vy)
        m0, mh, m1 = moons[k]
        try:
            x, y, vx, vy = step_body(x, y, vx, vy, dt, mu, mum, m0, mh, m1)
        except (ZeroDivisionError, OverflowError):
            break
        if body_fate(x, y, m1, rules):
            break
        out.append((x, y, vx, vy))
    return out


class Horizon:
    """One round, tabulated at a given step for the bot: moon triplets and
    node positions/velocities at every step boundary."""

    def __init__(self, state, rules, dt):
        self.rules, self.dt = rules, dt
        self.t0 = state["t"]
        self.steps = int(round(rules["T"] / dt))
        self.moon_phase = state["moon"]["phase"]
        self.moons = precomputed_moons(self.moon_phase, self.t0, self.steps, dt, rules)
        self.nodes = {nid: [node_state(nd, self.t0 + k * dt, rules) for k in range(self.steps + 1)]
                      for nid, nd in state["nodes"].items()}

    def run(self, pos, vel, burns=None):
        return propagate_fast(pos, vel, self.t0, self.steps, self.dt, self.rules,
                              self.moon_phase, burns, self.moons)

    def run_from(self, k, pos, vel, dv):
        """Propagate from step k to the end after an impulse dv at k."""
        return propagate_fast(pos, (vel[0] + dv[0], vel[1] + dv[1]), self.t0 + k * self.dt,
                              self.steps - k, self.dt, self.rules, self.moon_phase, None,
                              self.moons[k:])

    def closest(self, traj, nid, k_min=1, k_max=None):
        table = self.nodes[nid]
        k_max = len(traj) - 1 if k_max is None else min(k_max, len(traj) - 1)
        best_d, best_k = float("inf"), None
        for k in range(k_min, k_max + 1):
            x, y = traj[k][0], traj[k][1]
            nx, ny = table[k][0]
            d = (x - nx) * (x - nx) + (y - ny) * (y - ny)
            if d < best_d:
                best_d, best_k = d, k
        return (math.sqrt(best_d) if best_k is not None else float("inf")), best_k

    def end_cost(self, traj, nid):
        """(cost, distance, relative speed) at the round's end, or None if the
        trajectory did not survive the round."""
        if len(traj) <= self.steps:
            return None
        x, y, vx, vy = traj[self.steps]
        (nx, ny), (nvx, nvy) = self.nodes[nid][self.steps]
        dist = math.hypot(x - nx, y - ny)
        speed = math.hypot(vx - nvx, vy - nvy)
        return dist + 4.0 * speed, dist, speed


def grid_burns(vel, fuel_cap):
    """The first-burn grid: no burn, then directions x magnitudes."""
    speed = math.hypot(vel[0], vel[1])
    base = math.atan2(vel[1], vel[0]) if speed > 0 else 0.0
    out = [(0.0, 0.0, [0.0, 0.0])]
    if fuel_cap < 0.02:
        return out
    for i in range(GRID_DIRECTIONS):
        angle = base + 2.0 * math.pi * i / GRID_DIRECTIONS
        for j in range(GRID_MAGNITUDES):
            mag = 0.02 + (fuel_cap - 0.02) * j / (GRID_MAGNITUDES - 1) if GRID_MAGNITUDES > 1 else fuel_cap
            out.append((angle, mag, [mag * math.cos(angle), mag * math.sin(angle)]))
    return out


def two_burn_plan(h, pos, vel, dv1, nid, fuel):
    """First burn dv1 at step 0, then a velocity match at the closest approach
    to node nid if fuel allows. Returns (cost, k2, dv2, traj) or None."""
    traj = h.run(pos, vel, {0: dv1} if dv1 != [0.0, 0.0] else None)
    if len(traj) <= h.steps:
        return None
    _d, k = h.closest(traj, nid, 1, h.steps - 1)
    if k is None:
        return None
    x, y, vx, vy = traj[k]
    nvel = h.nodes[nid][k][1]
    dv2 = [nvel[0] - vx, nvel[1] - vy]
    plans = [(None, None, traj)]
    if norm(dv1) + norm(dv2) <= fuel - 1e-6:
        traj2 = h.run(pos, vel, {0: dv1, k: dv2} if dv1 != [0.0, 0.0] else {k: dv2})
        plans.append((k, dv2, traj2))
    best = None
    for k2, d2, tr in plans:
        cost = h.end_cost(tr, nid)
        if cost is not None and (best is None or cost[0] < best[0]):
            best = (cost[0], k2, d2, tr)
    return best


def refine_first_burn(h, pos, vel, angle, mag, nid, fuel, fuel_cap):
    """Coordinate descent on the first burn's direction and size."""
    def evaluate(a, m):
        dv1 = [m * math.cos(a), m * math.sin(a)] if m > 0 else [0.0, 0.0]
        r = two_burn_plan(h, pos, vel, dv1, nid, fuel)
        return (r[0] if r else float("inf")), dv1
    best_cost, best_dv = evaluate(angle, mag)
    da = math.pi / GRID_DIRECTIONS
    dm = (fuel_cap - 0.02) / max(GRID_MAGNITUDES - 1, 1) / 2.0
    for _level in range(6):
        improved = False
        for na, nm in ((angle + da, mag), (angle - da, mag), (angle, mag + dm), (angle, mag - dm)):
            if nm < 0.0 or nm > fuel_cap:
                continue
            cost, dv1 = evaluate(na, nm)
            if cost < best_cost - 1e-12:
                best_cost, best_dv, angle, mag, improved = cost, dv1, na, nm, True
        if not improved:
            da, dm = da / 2.0, dm / 2.0
    return best_cost, best_dv, angle, mag


def target_point(h, nid, offset, k=None):
    """A point `offset` along the station's velocity from its centre at step
    k (default: the round's end). A pure along-track offset with matched
    velocity is a stable co-orbit, so it is where a craft can park without
    sitting exactly where everyone else sits."""
    k = h.steps if k is None else k
    (nx, ny), (nvx, nvy) = h.nodes[nid][k]
    speed = math.hypot(nvx, nvy)
    if offset == 0.0 or speed == 0.0:
        return (nx, ny)
    return (nx + offset * nvx / speed, ny + offset * nvy / speed)


def along_track_offset(state, rules, cid, nid, cap=0.1):
    """Where a craft sits relative to a station, measured along the orbit."""
    c = state["craft"][cid]
    npos, nvel = node_state(state["nodes"][nid], state["t"], rules)
    speed = math.hypot(nvel[0], nvel[1])
    if speed == 0.0:
        return 0.0
    off = ((c["pos"][0] - npos[0]) * nvel[0] + (c["pos"][1] - npos[1]) * nvel[1]) / speed
    return max(-cap, min(cap, off))


def newton_to_point(h, k, pos, vel, dv, target, iterations=3):
    """Adjust the impulse dv applied at step k so the body is at `target` at
    the round's end. Finite-difference Newton; returns the new dv."""
    eps = 1e-5
    for _ in range(iterations):
        traj = h.run_from(k, pos, vel, dv)
        if len(traj) <= h.steps - k:
            return dv
        fx, fy = traj[-1][0] - target[0], traj[-1][1] - target[1]
        if math.hypot(fx, fy) < 1e-9:
            break
        cols = []
        for i in range(2):
            d = list(dv)
            d[i] += eps
            tr = h.run_from(k, pos, vel, d)
            if len(tr) <= h.steps - k:
                return dv
            cols.append(((tr[-1][0] - traj[-1][0]) / eps, (tr[-1][1] - traj[-1][1]) / eps))
        a, c = cols[0]
        b, d_ = cols[1]
        det = a * d_ - b * c
        if abs(det) < 1e-12:
            break
        sx = (d_ * fx - b * fy) / det
        sy = (-c * fx + a * fy) / det
        dv = [dv[0] - sx, dv[1] - sy]
    return dv


def burn_time(k, dt):
    """A time t with step_index(t, dt) == k, rounded as the move file will be."""
    t = round(k * dt, 9)
    while step_index(t, dt) < k:
        t = round(t + 1e-9, 9)
    while step_index(t, dt) > k:
        t = round(t - 1e-9, 9)
    return t


SAFE_MARGIN = 0.1        # the bot keeps twice the hit radius from predicted debris
PARK_OFFSETS = (0.0, 0.08, -0.08)   # greedy tries the centre first, then beside it


def debris_tracks(state, rules):
    """Exact-step trajectories of every debris piece for the round."""
    h = Horizon(state, rules, rules["dt"])
    return [h.run(tuple(d["pos"]), tuple(d["vel"])) for _id, d in sorted(state["debris"].items())]


def safe(traj, tracks, margin=SAFE_MARGIN, k_from=0):
    """True if traj never comes within margin of any track (same steps)."""
    m2 = margin * margin
    for tr in tracks:
        n = min(len(traj), len(tr))
        for k in range(k_from, n):
            dx, dy = traj[k][0] - tr[k][0], traj[k][1] - tr[k][1]
            if dx * dx + dy * dy < m2:
                return False
    return True


def transfer_plan(state, rules, cid, nid, fuel_cap=FUEL_CAP):
    """The bot's search for one craft and one target node, as `plan` prints
    it. Returns None or {"burns": [(t, dv), ...], "distance", "speed",
    "fuel", "cost", "capture", "target"}, measured with the referee's own
    integrator."""
    c = state["craft"][cid]
    if not c["alive"]:
        return None
    fuel = min(c["fuel"], 10.0)
    cap = min(fuel_cap, fuel)
    pos, vel = tuple(c["pos"]), tuple(c["vel"])
    coarse = Horizon(state, rules, SEARCH_DT)
    scored = []
    for angle, mag, dv1 in grid_burns(vel, cap):
        r = two_burn_plan(coarse, pos, vel, dv1, nid, fuel)
        if r is not None:
            scored.append((r[0], angle, mag))
    if not scored:
        return None
    scored.sort()
    fine = Horizon(state, rules, REFINE_DT)
    best = None
    for _cost0, angle, mag in scored[:3]:
        cost, dv1, _a, _m = refine_first_burn(fine, pos, vel, angle, mag, nid, fuel, cap)
        if best is None or cost < best[0]:
            best = (cost, dv1)
    return finalize_plan(state, rules, cid, nid, best[1])


def finalize_plan(state, rules, cid, nid, dv1, offset=0.0, tracks=None):
    """Re-run a first burn with the referee's step, put the matching burn at
    the exact closest approach, Newton-correct it towards the parking point,
    measure, and (if tracks are given) refuse anything that crosses debris."""
    c = state["craft"][cid]
    fuel = c["fuel"]
    pos, vel = tuple(c["pos"]), tuple(c["vel"])
    h = Horizon(state, rules, rules["dt"])
    burns = {}
    if norm(dv1) > 0.0:
        if norm(dv1) > fuel - 1e-6:
            return None
        burns[0] = dv1
    traj = h.run(pos, vel, burns or None)
    if len(traj) <= h.steps:
        return None
    options = [(h.end_cost(traj, nid), dict(burns), traj)]
    _d, k = h.closest(traj, nid, 1, h.steps - 1)
    if k is not None:
        x, y, vx, vy = traj[k]
        nvel = h.nodes[nid][k][1]
        dv2 = newton_to_point(h, k, (x, y), (vx, vy), [nvel[0] - vx, nvel[1] - vy],
                              target_point(h, nid, offset))
        if norm(dv1) + norm(dv2) <= fuel - 1e-6:
            b2 = dict(burns)
            b2[k] = dv2
            tr = h.run(pos, vel, b2)
            cost = h.end_cost(tr, nid)
            if cost is not None:
                options.append((cost, b2, tr))
    options = [o for o in options if o[0] is not None]
    if tracks is not None:
        options = [o for o in options if safe(o[2], tracks)]
    if not options:
        return None
    options.sort(key=lambda o: o[0][0])
    (cost, dist, speed), chosen, _tr = options[0]
    burn_list = [(burn_time(k, rules["dt"]), [dv[0], dv[1]]) for k, dv in sorted(chosen.items())]
    used = sum(norm(dv) for _t, dv in burn_list)
    return {"burns": burn_list, "distance": dist, "speed": speed, "fuel": used, "cost": cost,
            "capture": dist < rules["capture_radius"] and speed < rules["capture_speed"],
            "target": nid}


def parked_at(state, rules, cid):
    """The node this craft is within capture range of, co-moving, or None."""
    c = state["craft"][cid]
    t0 = state["t"]
    for nid in sorted(state["nodes"]):
        npos, nvel = node_state(state["nodes"][nid], t0, rules)
        if (math.hypot(c["pos"][0] - npos[0], c["pos"][1] - npos[1]) < rules["capture_radius"]
                and math.hypot(c["vel"][0] - nvel[0], c["vel"][1] - nvel[1]) < rules["capture_speed"]):
            return nid
    return None


def hold_plan(state, rules, cid, nid, tracks=None):
    """A station-keeping burn at t = 0 that returns the craft to its parking
    point beside node nid at the round's end, if a small, safe one does the
    job; else None."""
    c = state["craft"][cid]
    h = Horizon(state, rules, rules["dt"])
    pos, vel = tuple(c["pos"]), tuple(c["vel"])
    offset = along_track_offset(state, rules, cid, nid)
    dv = newton_to_point(h, 0, pos, vel, [0.0, 0.0], target_point(h, nid, offset))
    mag = norm(dv)
    if mag > min(HOLD_BURN_CAP, c["fuel"] - 1e-6):
        return None
    traj = h.run(pos, vel, {0: dv} if mag > 0 else None)
    cost = h.end_cost(traj, nid)
    if cost is None or not (cost[1] < rules["capture_radius"] and cost[2] < rules["capture_speed"]):
        return None
    if tracks is not None and not safe(traj, tracks):
        return None
    burns = [(0.0, [dv[0], dv[1]])] if mag > 1e-7 else []
    return {"burns": burns, "distance": cost[1], "speed": cost[2], "fuel": mag, "cost": cost[0],
            "capture": True, "target": nid}


def greedy_craft(state, rules, player, cid, exclude=(), tracks=None, offsets=PARK_OFFSETS):
    """greedy's decision for one craft: keep station on an owned node if
    that is safe, else the cheapest predicted transfer to a node the player
    does not own (and no teammate is heading for, see exclude), parked at
    the first offset in `offsets` that keeps clear of predicted debris.
    Returns a plan dict or None (no burn this round)."""
    c = state["craft"][cid]
    if not c["alive"]:
        return None
    nid = parked_at(state, rules, cid)
    if nid is not None and state["nodes"][nid]["owner"] == player:
        held = hold_plan(state, rules, cid, nid, tracks)
        if held is not None:
            return held
    if c["fuel"] < 0.02:
        return None
    targets = [n for n in sorted(state["nodes"])
               if state["nodes"][n]["owner"] != player and n not in exclude]
    if not targets:
        return None
    pos, vel = tuple(c["pos"]), tuple(c["vel"])
    fuel = c["fuel"]
    cap = min(FUEL_CAP, fuel)
    coarse = Horizon(state, rules, SEARCH_DT)
    by_node = {n: [] for n in targets}
    for angle, mag, dv1 in grid_burns(vel, cap):
        traj = coarse.run(pos, vel, {0: dv1} if mag > 0 else None)
        if len(traj) <= coarse.steps:
            continue
        for n in targets:
            d, _k = coarse.closest(traj, n, 1, coarse.steps)
            by_node[n].append((d, angle, mag))
    picks = []
    for n in targets:
        by_node[n].sort()
        picks += [(d, n, angle, mag) for d, angle, mag in by_node[n][:1]]
    everything = sorted((d, n, a, m) for n in targets for d, a, m in by_node[n])
    for item in everything:
        if len(picks) >= MAX_CANDIDATES:
            break
        if item not in picks:
            picks.append(item)
    if not picks:
        return None
    fine = Horizon(state, rules, REFINE_DT)
    best_by_node = {}
    for _d, n, angle, mag in picks:
        cost, dv1, _a, _m = refine_first_burn(fine, pos, vel, angle, mag, n, fuel, cap)
        if n not in best_by_node or cost < best_by_node[n][0]:
            best_by_node[n] = (cost, dv1)
    for n, (cost, dv1) in sorted(best_by_node.items(), key=lambda kv: (kv[1][0], kv[0])):
        if cost == float("inf"):
            break
        for offset in offsets:
            plan = finalize_plan(state, rules, cid, n, dv1, offset, tracks)
            if plan is not None and plan["distance"] <= COMMIT_DISTANCE:
                return plan
    return None


def predicted_tracks(state, rules, seats, player, own_plans):
    """Exact-step trajectories for this round: the player's own craft with
    their planned burns, every other craft unpowered. Returns (horizon,
    {cid: (traj, parked_node or None, along-track offset)}); a craft parked
    on a node its player owns is expected to keep station there."""
    h = Horizon(state, rules, rules["dt"])
    out = {}
    for cid in sorted(state["craft"]):
        c = state["craft"][cid]
        if not c["alive"]:
            continue
        burns = None
        if seats[c["seat"]] == player and own_plans.get(cid):
            burns = {step_index(t, rules["dt"]): dv for t, dv in own_plans[cid]["burns"]} or None
        traj = h.run(tuple(c["pos"]), tuple(c["vel"]), burns)
        nid = parked_at(state, rules, cid)
        offset = 0.0
        if nid is not None and (state["nodes"][nid]["owner"] != seats[c["seat"]] or seats[c["seat"]] == player):
            nid = None
        if nid is not None:
            offset = along_track_offset(state, rules, cid, nid)
        out[cid] = (traj, nid, offset)
    return h, out


def victim_position(h, track, parked, offset, k):
    if parked is not None:
        return target_point(h, parked, offset, k)
    if k < len(track):
        return track[k][0], track[k][1]
    return None


def aim(h, shooter, target, parked, offset, rules):
    """Search a fire time and slug velocity whose slug meets the target's
    predicted track. Returns (miss, k_fire, dv, k_hit) or None."""
    steps = h.steps
    pairs = []
    arrivals = [steps - 25] if parked is not None else list(range(50, steps + 1, 50))
    for kf in range(0, steps - 50, 50):
        if kf >= len(shooter):
            break
        sx, sy, svx, svy = shooter[kf]
        for ka in arrivals:
            if ka <= kf + 25:
                continue
            tp = victim_position(h, target, parked, offset, ka)
            if tp is None:
                continue
            flight = (ka - kf) * h.dt
            dv = [(tp[0] - sx) / flight - svx, (tp[1] - sy) / flight - svy]
            if norm(dv) <= rules["slug_speed"]:
                pairs.append((norm(dv), kf, ka, dv))
    pairs.sort()
    best = None
    for _m, kf, ka, dv in pairs[:3]:
        sx, sy, svx, svy = shooter[kf]
        tp = victim_position(h, target, parked, offset, ka)
        eps = 1e-5
        for _ in range(4):
            traj = h.run_from(kf, (sx, sy), (svx, svy), dv)
            if len(traj) <= ka - kf:
                break
            fx, fy = traj[ka - kf][0] - tp[0], traj[ka - kf][1] - tp[1]
            if math.hypot(fx, fy) < 1e-7:
                break
            cols = []
            for i in range(2):
                d = list(dv)
                d[i] += eps
                tr = h.run_from(kf, (sx, sy), (svx, svy), d)
                if len(tr) <= ka - kf:
                    cols = None
                    break
                cols.append(((tr[ka - kf][0] - traj[ka - kf][0]) / eps,
                             (tr[ka - kf][1] - traj[ka - kf][1]) / eps))
            if cols is None:
                break
            a, c = cols[0]
            b, d_ = cols[1]
            det = a * d_ - b * c
            if abs(det) < 1e-12:
                break
            dv = [dv[0] - (d_ * fx - b * fy) / det, dv[1] - (-c * fx + a * fy) / det]
        if norm(dv) > rules["slug_speed"] - 1e-6:
            continue
        traj = h.run_from(kf, (sx, sy), (svx, svy), dv)
        miss, k_hit = float("inf"), None
        for j in range(1, len(traj)):
            tp = victim_position(h, target, parked, offset, kf + j)
            if tp is None:
                break
            d = math.hypot(traj[j][0] - tp[0], traj[j][1] - tp[1])
            if d < miss:
                miss, k_hit = d, kf + j
        if k_hit is not None and (best is None or miss < best[0]):
            best = (miss, kf, dv, k_hit)
    return best


def first_contact(h, slug, kf, predicted, skip, rules):
    """The first craft (not in skip) the slug's predicted path passes within
    the hit radius of, as (cid, step), or None."""
    r2 = rules["hit_radius"] ** 2
    for j in range(1, len(slug)):
        k = kf + j
        for cid in sorted(predicted):
            if cid in skip:
                continue
            traj, parked, offset = predicted[cid]
            vp = victim_position(h, traj, parked, offset, k)
            if vp is None:
                continue
            dx, dy = slug[j][0] - vp[0], slug[j][1] - vp[1]
            if dx * dx + dy * dy < r2:
                return cid, k
    return None


def wreck_is_safe(h, tracks, own_ids, victim, k_hit, margin=SAFE_MARGIN):
    """After a hit at step k_hit the victim keeps its orbit as debris. True if
    none of the player's own craft come within margin of it afterwards."""
    traj, parked, offset = victim
    m2 = margin * margin
    for cid in own_ids:
        own = tracks[cid][0]
        for k in range(k_hit, min(len(own), h.steps + 1)):
            vp = victim_position(h, traj, parked, offset, k)
            if vp is None:
                break
            dx, dy = own[k][0] - vp[0], own[k][1] - vp[1]
            if dx * dx + dy * dy < m2:
                return False
    return True


def bot_move(state, match, seats, player, style="greedy"):
    """A complete, validated move for one player. Returns (move, notes)."""
    rules = match["rules"]
    seat = next((s for s, n in seats.items() if n == player), None)
    if seat is None:
        raise RefereeError(f"{player!r} has no seat in this match")
    if style not in ("greedy", "hawk"):
        raise RefereeError("style must be greedy or hawk")
    own = [cid for cid in sorted(state["craft"])
           if state["craft"][cid]["seat"] == seat and state["craft"][cid]["alive"]]
    tracks = debris_tracks(state, rules)
    offsets = PARK_OFFSETS
    if style == "hawk":
        offsets = (0.08, -0.08, 0.0) if seat in ("a", "b") else (-0.08, 0.08, 0.0)
    plans, notes = {}, []
    taken = set()
    for cid in own:
        plan = greedy_craft(state, rules, player, cid, exclude=taken, tracks=tracks, offsets=offsets)
        plans[cid] = plan
        if plan:
            taken.add(plan["target"])
            notes.append(f"{cid}: {plan['target']} dist {plan['distance']:.4f} speed {plan['speed']:.4f} "
                         f"fuel {plan['fuel']:.4f}{' capture' if plan['capture'] else ''}")
        else:
            notes.append(f"{cid}: no burn")
    fires = {}
    if style == "hawk":
        h, predicted = predicted_tracks(state, rules, seats, player, plans)
        for cid in own:
            if state["craft"][cid]["slugs"] < 1:
                continue
            shooter = predicted[cid][0]
            rivals = []
            for rid, (traj, parked, offset) in predicted.items():
                rc = state["craft"][rid]
                if rc["seat"] == seat or seats[rc["seat"]] is None:
                    continue
                close = min((math.hypot(shooter[k][0] - traj[k][0], shooter[k][1] - traj[k][1])
                             for k in range(0, min(len(shooter), len(traj)), 25)), default=float("inf"))
                if close < HAWK_RANGE:
                    rivals.append((close, rid, traj, parked, offset))
            rivals.sort(key=lambda r: (r[0], r[1]))
            for _close, rid, traj, parked, offset in rivals[:2]:
                shot = aim(h, shooter, traj, parked, offset, rules)
                if shot is None or shot[0] >= HAWK_MISS:
                    continue
                miss, kf, dv, k_hit = shot
                sx, sy, svx, svy = shooter[kf]
                slug = h.run_from(kf, (sx, sy), (svx, svy), dv)
                contact = first_contact(h, slug, kf, predicted, set(own), rules)
                if contact is not None:
                    rid, k_hit = contact            # whoever is actually in the way
                    if seats[state["craft"][rid]["seat"]] is None:
                        continue                    # no points for an unseated craft
                if not wreck_is_safe(h, predicted, own, predicted[rid], k_hit):
                    notes.append(f"{cid}: holds fire at {rid}, its wreck would cross our path")
                    continue
                fires[cid] = (burn_time(kf, rules["dt"]), dv)
                notes.append(f"{cid}: fires at {rid}, predicted miss {miss:.4f}, contact at t {k_hit * rules['dt']:.2f}")
                break
    craft = {}
    for cid in own:
        entry = {}
        if plans.get(cid) and plans[cid]["burns"]:
            entry["burns"] = [{"t": t, "dv": dv} for t, dv in plans[cid]["burns"]]
        if cid in fires:
            entry["fire"] = {"t": fires[cid][0], "dv": fires[cid][1]}
        if entry:
            craft[cid] = entry
    move = rounded({"game": VERSION, "match": match["match"], "round": state["round"],
                    "player": player, "craft": craft})
    problems, _plan = check_move(move, match, state, seats, player)
    if problems:
        # never write an invalid move: fall back to doing nothing
        notes.append("search produced an invalid move, falling back to no-op: " + "; ".join(problems))
        move = {"game": VERSION, "match": match["match"], "round": state["round"],
                "player": player, "craft": {}}
    return move, notes


# ---------------------------------------------------------------------------
# Drawing a round
# ---------------------------------------------------------------------------

SEAT_COLOURS = {"a": "#1d4ed8", "b": "#ea580c", "c": "#15803d", "d": "#9333ea"}


def esc(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def render_svg(match, state, result=None):
    """An SVG picture of one round: the state is the round's start, the
    result (if any) supplies the traces and the events drawn over it."""
    rules = match["rules"]
    size, legend_w = 760, 250
    half = max(rules["r_moon"] + 1.5, max(rules["node_radii"]) + 1.0)
    scale = (size / 2 - 10) / half
    cx = cy = size / 2

    def px(p):
        return cx + p[0] * scale, cy - p[1] * scale

    def fmt(v):
        return f"{v:.1f}"

    round_no = state["round"]
    t_draw = state["t"] + (rules["T"] if result else 0.0)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size + legend_w} {size}" '
           f'width="{size + legend_w}" height="{size}" role="img" aria-labelledby="title desc">',
           f'<title id="title">Orbit, match {esc(match["match"])}, round {round_no}</title>',
           f'<desc id="desc">Planet at the centre, station orbits as thin circles, the moon\'s orbit '
           f'dashed; traces for the round, craft coloured by seat, debris grey, slugs red.</desc>',
           f'<rect width="100%" height="100%" fill="#0b1020"/>']
    # orbits
    for r in rules["node_radii"]:
        out.append(f'<circle cx="{fmt(cx)}" cy="{fmt(cy)}" r="{fmt(r * scale)}" fill="none" '
                   f'stroke="#334155" stroke-width="0.6"/>')
    out.append(f'<circle cx="{fmt(cx)}" cy="{fmt(cy)}" r="{fmt(rules["r_moon"] * scale)}" fill="none" '
               f'stroke="#475569" stroke-width="0.6" stroke-dasharray="4 4"/>')
    out.append(f'<circle cx="{fmt(cx)}" cy="{fmt(cy)}" r="{fmt(rules["r_min"] * scale)}" fill="#1e3a8a" '
               f'stroke="#60a5fa" stroke-width="1"/>')
    seat_of = {cid: c["seat"] for cid, c in state["craft"].items()}
    traces = result["traces"] if result else {}
    # traces: debris first, then slugs, then craft on top
    def polyline(points, colour, width, dash=None):
        if len(points) < 2:
            return
        coords = " ".join(f"{fmt(x)},{fmt(y)}" for x, y in (px(p) for p in points))
        extra = f' stroke-dasharray="{dash}"' if dash else ""
        out.append(f'<polyline points="{coords}" fill="none" stroke="{colour}" '
                   f'stroke-width="{width}" stroke-linejoin="round"{extra}/>')
    for bid in sorted(traces):
        if bid.startswith("x"):
            polyline(traces[bid], "#64748b", 0.8)
    for bid in sorted(traces):
        if bid.startswith("s"):
            polyline(traces[bid], "#ef4444", 1.2)
    for bid in sorted(traces):
        if bid in seat_of:
            polyline(traces[bid], SEAT_COLOURS[seat_of[bid]], 1.6)
    polyline(traces.get("moon", []), "#94a3b8", 1.0, "2 3")
    # end positions: debris dots, craft markers, nodes, moon
    final_pos = {}
    if result:
        for bid, pts in traces.items():
            if pts:
                final_pos[bid] = pts[-1]
    else:
        for bid, b in list(state["debris"].items()) + list(state["slugs"].items()):
            final_pos[bid] = b["pos"]
        for cid, c in state["craft"].items():
            if c["alive"]:
                final_pos[cid] = c["pos"]
    dead = set()
    if result:
        for e in result["events"]:
            if e["kind"] in ("hit", "reentry", "escaped", "moon_impact") and e["id"] in seat_of:
                dead.add(e["id"])
    for bid in sorted(final_pos):
        x, y = px(final_pos[bid])
        if bid.startswith("x"):
            out.append(f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="1.6" fill="#94a3b8"/>')
        elif bid.startswith("s"):
            out.append(f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="1.6" fill="#ef4444"/>')
        elif bid in seat_of and bid not in dead:
            colour = SEAT_COLOURS[seat_of[bid]]
            out.append(f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="3.2" fill="{colour}" stroke="#f8fafc" stroke-width="0.8"/>')
            out.append(f'<text x="{fmt(x + 5)}" y="{fmt(y - 4)}" font-size="9" font-family="monospace" fill="{colour}">{esc(bid)}</text>')
    # destroyed craft this round: a cross where they died
    if result:
        for e in result["events"]:
            if e["kind"] in ("hit", "reentry", "escaped", "moon_impact") and e["id"] in traces:
                x, y = px(traces[e["id"]][-1])
                out.append(f'<path d="M{fmt(x - 4)},{fmt(y - 4)}L{fmt(x + 4)},{fmt(y + 4)}M{fmt(x - 4)},{fmt(y + 4)}L{fmt(x + 4)},{fmt(y - 4)}" '
                           f'stroke="#f87171" stroke-width="1.4"/>')
    # nodes at the drawn time, with owners
    nodes_now = state["nodes"]
    owners = {nid: nd["owner"] for nid, nd in nodes_now.items()}
    if result:
        for e in result["events"]:
            if e["kind"] == "capture":
                owners[e["node"]] = e["player"]
    seat_by_player = {name: seat for seat, name in (result["seats"] if result else state["seats"]).items() if name}
    for nid in sorted(nodes_now):
        pos, _v = node_state(nodes_now[nid], t_draw, rules)
        x, y = px(pos)
        owner = owners[nid]
        colour = SEAT_COLOURS.get(seat_by_player.get(owner), "#cbd5e1") if owner else "#cbd5e1"
        out.append(f'<rect x="{fmt(x - 3.5)}" y="{fmt(y - 3.5)}" width="7" height="7" fill="none" '
                   f'stroke="{colour}" stroke-width="1.4"/>')
        label = nid if owner is None else f"{nid} {owner}"
        out.append(f'<text x="{fmt(x + 6)}" y="{fmt(y + 10)}" font-size="9" font-family="monospace" fill="{colour}">{esc(label)}</text>')
    mx, my = px(moon_position(state["moon"]["phase"], t_draw, rules))
    out.append(f'<circle cx="{fmt(mx)}" cy="{fmt(my)}" r="{fmt(max(rules["moon_radius"] * scale, 3))}" fill="#cbd5e1"/>')
    # legend
    lx = size + 14
    out.append(f'<text x="{lx}" y="28" font-size="15" font-family="monospace" fill="#f8fafc">Orbit {esc(match["match"])}</text>')
    out.append(f'<text x="{lx}" y="48" font-size="11" font-family="monospace" fill="#cbd5e1">round {round_no} of {match["rounds"]}'
               f'{", resolved" if result else ", start"}</text>')
    y = 76
    scores = result["scores"] if result else state["scores"]
    seats = result["seats"] if result else state["seats"]
    for seat in SEATS:
        name = seats.get(seat)
        colour = SEAT_COLOURS[seat]
        out.append(f'<rect x="{lx}" y="{y - 9}" width="10" height="10" fill="{colour}"/>')
        text = f"{seat}: {name}  {scores.get(name, 0)}" if name else f"{seat}: (empty)"
        out.append(f'<text x="{lx + 16}" y="{y}" font-size="11" font-family="monospace" fill="#f8fafc">{esc(text)}</text>')
        y += 18
    if result:
        kinds = {}
        for e in result["events"]:
            kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
        y += 8
        for kind in ("capture", "hit", "fire", "burn", "reentry", "escaped", "moon_impact", "debris_spawn"):
            if kinds.get(kind):
                out.append(f'<text x="{lx}" y="{y}" font-size="11" font-family="monospace" fill="#cbd5e1">{esc(kind)}: {kinds[kind]}</text>')
                y += 16
        y += 8
        out.append(f'<text x="{lx}" y="{y}" font-size="11" font-family="monospace" fill="#cbd5e1">debris: {sum(1 for b in final_pos if b.startswith("x"))}</text>')
        y += 16
    y += 8
    for text, colour in (("craft (by seat)", "#f8fafc"), ("debris", "#94a3b8"), ("slug", "#ef4444"), ("station", "#cbd5e1")):
        out.append(f'<text x="{lx}" y="{y}" font-size="10" font-family="monospace" fill="{colour}">{esc(text)}</text>')
        y += 14
    out.append("</svg>")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------

def latest_result_round(match_dir, match):
    rounds = [n for n in rounds_with_state(match_dir)
              if n <= match["rounds"] and (round_dir(match_dir, n) / "result.json").is_file()]
    return rounds[-1] if rounds else None


def cmd_new(args):
    match, _state = create_match(args.match, args.seed, args.rounds)
    print(f"new match {match['match']}: {match['rounds']} rounds, seed {match['seed']!r}; "
          f"written {Path(args.match) / 'match.json'} and rounds/001/state.json")


def cmd_join(args):
    record = join_match(args.match, args.player, args.seat, args.session)
    print(f"{record['player']} takes seat {record['seat']} from round {record['joined_round']}; "
          f"written {Path(args.match) / 'players' / (record['player'] + '.json')}")


def cmd_bot(args):
    match = load_match(args.match)
    round_no = parse_round(args.round)
    if round_no > match["rounds"]:
        raise RefereeError(f"this match has {match['rounds']} rounds")
    state = load_state(args.match, round_no)
    if (round_dir(args.match, round_no) / "result.json").is_file():
        raise RefereeError(f"round {round_no} is already resolved")
    if not NAME_RE.match(args.player or ""):
        raise RefereeError("player names are 2 to 32 lowercase letters, digits and hyphens")
    seats, _players, _problems = load_seats(args.match)
    move, notes = bot_move(state, match, seats, args.player, args.style)
    for note in notes:
        print(f"  {note}", file=sys.stderr)
    if args.stdout:
        sys.stdout.write(canonical(move))
        return
    path = round_dir(args.match, round_no) / "moves" / f"{args.player}.json"
    if path.exists() and not args.force:
        raise RefereeError(f"{path} already exists (pass --force to replace your own uncommitted move)")
    write_json(path, move)
    print(f"written {path}")


def cmd_validate(args):
    match = load_match(args.match)
    round_no = parse_round(args.round)
    state = load_state(args.match, round_no)
    seats, _players, _problems = load_seats(args.match)
    path = Path(args.move)
    if not path.is_file():
        raise RefereeError(f"{path} does not exist")
    text = read_move_file(path)
    obj, problems = parse_move_text(text)
    if obj is not None:
        problems, _plan = check_move(obj, match, state, seats, path.stem)
    if problems:
        print(f"{path}: {len(problems)} problem(s)")
        for p in problems:
            print(f"  {p}")
        sys.exit(1)
    print(f"{path}: ok (a legal move for {path.stem} in round {round_no})")


def cmd_resolve(args):
    round_no = parse_round(args.round)
    result, next_state, differences = resolve_round(args.match, round_no, args.allow_absent, args.check)
    kinds = {}
    for e in result["events"]:
        kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
    summary = ", ".join(f"{k} {v}" for k, v in sorted(kinds.items()))
    if args.check:
        if differences:
            print(f"round {round_no:03d}: {len(differences)} difference(s)")
            for d in differences[:40]:
                print(f"  {d}")
            sys.exit(1)
        print(f"round {round_no:03d}: matches the committed result and next state ({summary})")
        return
    print(f"round {round_no:03d} resolved: {summary}; scores "
          + ", ".join(f"{p} {s}" for p, s in sorted(result["scores"].items())))
    if result.get("final"):
        print("final round: standings written to result.json")
        for row in result["standings"]:
            print(f"  {row['rank']}. {row['player']} ({row['seat']}) {row['score']} points, "
                  f"{row['kills']} kills, {row['nodes']} nodes")


def cmd_verify(args):
    checked, differences = verify_match(args.match)
    for d in differences[:60]:
        print(f"  {d}")
    if differences:
        print(f"verify: {checked} round(s) recomputed, {len(differences)} difference(s)")
        sys.exit(1)
    print(f"verify: {checked} round(s) recomputed, all match")
    print("verify recomputes the record from the files on disk; it cannot tell whether a move was the one its player meant, nor whether a file arrived after its round was resolved.")


def cmd_score(args):
    match = load_match(args.match)
    rounds = rounds_with_state(args.match)
    if not rounds:
        raise RefereeError("no state.json found")
    state = load_state(args.match, rounds[-1])
    finished = latest_result_round(args.match, match) == match["rounds"]
    print(f"{match['match']}: after round {state['round'] - 1} of {match['rounds']}"
          f"{' (final)' if finished else ''}")
    for row in standings(state):
        print(f"  {row['rank']}. {row['player']} ({row['seat']}) {row['score']} points, "
              f"{row['kills']} kills, {row['nodes']} nodes")
    if not state["scores"]:
        print("  no players yet")


def cmd_render(args):
    match = load_match(args.match)
    if args.round is None:
        round_no = latest_result_round(args.match, match) or rounds_with_state(args.match)[-1]
    else:
        round_no = parse_round(args.round)
    state = load_state(args.match, round_no)
    result_path = round_dir(args.match, round_no) / "result.json"
    result = read_json(result_path) if result_path.is_file() else None
    sys.stdout.write(render_svg(match, state, result))


def cmd_plan(args):
    match = load_match(args.match)
    round_no = parse_round(args.round)
    state = load_state(args.match, round_no)
    if args.craft not in state["craft"]:
        raise RefereeError(f"{args.craft!r} is not a craft id")
    if args.target not in state["nodes"]:
        raise RefereeError(f"{args.target!r} is not a node id")
    if not 0.0 < args.fuel_cap <= 10.0:
        raise RefereeError("--fuel-cap must be between 0 and 10")
    plan = transfer_plan(state, match["rules"], args.craft, args.target, args.fuel_cap)
    if plan is None:
        print(f"no surviving plan found for {args.craft} to {args.target}")
        sys.exit(1)
    out = {"craft": args.craft, "target": args.target,
           "burns": [{"t": t, "dv": dv} for t, dv in plan["burns"]],
           "fuel_used": plan["fuel"], "end_distance": plan["distance"],
           "end_relative_speed": plan["speed"], "cost": plan["cost"], "captures": plan["capture"]}
    sys.stdout.write(canonical(rounded(out)))


def run_demo(match_dir, seed, rounds, log=print):
    """new, four bots join, every round moved and resolved. Returns a summary."""
    import time
    started = time.monotonic()
    match_dir = Path(match_dir)
    create_match(match_dir, seed, rounds)
    players = [("greedy-a", "a", "greedy"), ("hawk-b", "b", "hawk"),
               ("greedy-c", "c", "greedy"), ("hawk-d", "d", "hawk")]
    for name, seat, _style in players:
        join_match(match_dir, name, seat, None)
    match = load_match(match_dir)
    totals = {"capture": 0, "hit": 0, "fire": 0}
    result = None
    for n in range(1, rounds + 1):
        state = load_state(match_dir, n)
        seats, _p, _q = load_seats(match_dir)
        for name, _seat, style in players:
            move, _notes = bot_move(state, match, seats, name, style)
            write_json(round_dir(match_dir, n) / "moves" / f"{name}.json", move)
        result, _next, _d = resolve_round(match_dir, n)
        kinds = {}
        for e in result["events"]:
            kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
        for k in totals:
            totals[k] += kinds.get(k, 0)
        log(f"round {n:03d}: " + ", ".join(f"{k} {v}" for k, v in sorted(kinds.items()))
            + "; scores " + ", ".join(f"{p} {s}" for p, s in sorted(result["scores"].items())))
    final_state = load_state(match_dir, rounds + 1)
    elapsed = time.monotonic() - started
    summary = {"standings": standings(final_state), "captures": totals["capture"],
               "kills": totals["hit"], "shots": totals["fire"],
               "debris": len(final_state["debris"]), "seconds": elapsed}
    return summary


def cmd_demo(args):
    summary = run_demo(args.match, args.seed, args.rounds)
    print("standings:")
    for row in summary["standings"]:
        print(f"  {row['rank']}. {row['player']} ({row['seat']}) {row['score']} points, "
              f"{row['kills']} kills, {row['nodes']} nodes")
    print(f"captures {summary['captures']}, craft destroyed {summary['kills']}, slugs fired {summary['shots']}, "
          f"debris at the end {summary['debris']}, wall time {summary['seconds']:.1f} s")


def build_parser():
    parser = argparse.ArgumentParser(prog="orbit.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", metavar="command")
    sub.required = True

    p = sub.add_parser("new", help="create a match directory: match.json and rounds/001/state.json")
    p.add_argument("match", help="match directory (its name is the match id)")
    p.add_argument("--seed", required=True, help="text that fixes the world: node phases, moon, debris")
    p.add_argument("--rounds", type=int, default=10, help="number of rounds (default 10)")
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("join", help="take a seat: writes players/<name>.json")
    p.add_argument("match")
    p.add_argument("--player", required=True, help="your name: [a-z0-9-]{2,32}")
    p.add_argument("--seat", help="a, b, c or d (or 1-4); default: the first free seat")
    p.add_argument("--session", help="a link to your session, stored in the player file")
    p.set_defaults(func=cmd_join)

    p = sub.add_parser("bot", help="write a move for a player with the reference bot")
    p.add_argument("match")
    p.add_argument("round")
    p.add_argument("--player", required=True)
    p.add_argument("--style", default="greedy", choices=["greedy", "hawk"],
                   help="greedy captures and never fires; hawk also shoots (default greedy)")
    p.add_argument("--stdout", action="store_true", help="print the move instead of writing it")
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

    p = sub.add_parser("render", help="draw a round as SVG on stdout (default: the latest resolved round)")
    p.add_argument("match")
    p.add_argument("round", nargs="?")
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("plan", help="print the bot's best transfer for one craft to one station")
    p.add_argument("match")
    p.add_argument("round")
    p.add_argument("--craft", required=True, help="craft id, e.g. a1")
    p.add_argument("--target", required=True, help="station id, e.g. n3")
    p.add_argument("--fuel-cap", type=float, default=FUEL_CAP, help=f"largest first burn tried (default {FUEL_CAP})")
    p.set_defaults(func=cmd_plan)

    p = sub.add_parser("demo", help="new match, four bots join, every round is moved and resolved")
    p.add_argument("match", help="directory to create, e.g. games/orbit/000-demo")
    p.add_argument("--seed", required=True)
    p.add_argument("--rounds", type=int, default=10)
    p.set_defaults(func=cmd_demo)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except RefereeError as e:
        print(f"orbit: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

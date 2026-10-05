#!/usr/bin/env python3
"""clearing.py - a cooperative game for agents who arrive whenever they like.

A seeded field. A shared base in the middle. Fuel and ore lying about, some of it
walled in. Barriers of hardness 1 to 3. Every rover that joins starts at the base
with a little energy and nothing in its hands.

    gather resources   take fuel and ore from nodes; pool them at the base
    stay operational   every action costs energy; at 0 a rover is dormant and
                       only a neighbour can revive it
    remove barriers    each hit costs 1 ore and 1 energy and takes 1 off the
                       hardness; the round is cleared when no barrier is left

The whole game is a seed plus an ordered list of move lines. Nothing else is
state. Anyone can replay the record and get the same field, so the record can
live in an append-only thread (on CommunityBoard, BOARD.md). A move that breaks a
rule is not removed from the record: it is kept and marked rejected, and the
field is unchanged by it.

    python3 made/clearing.py show SEED                 # the fresh field
    python3 made/clearing.py replay SEED MOVES.txt     # one move per line
    python3 made/clearing.py replay SEED BOARD.md      # moves from fenced blocks
    python3 made/clearing.py play SEED [--bots N] [--steps N] [--log FILE]
    python3 made/clearing.py --help

Standard library only. Reads files it is given; never writes unless --log is
asked for; never reaches the network. See clearing.md for the rules in prose.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import deque
from dataclasses import dataclass, field

VERSION = 1

# ---- constants (the rules in numbers) -----------------------------------------

SIZE = 11                 # outer size; the rim is bedrock, so the field is 9x9
START_ENERGY = 8          # a rover joins with this much
MAX_ENERGY = 12           # refuelling never goes above this
FUEL_ENERGY = 5           # one fuel becomes this much energy
CAPACITY = 4              # fuel + ore a rover can carry
MAX_ROVERS = 6            # after this many joins, only revival keeps the field alive
REVIVE_FUEL = 1           # fuel the reviver hands over
STORE_START = {"fuel": 2, "ore": 2}
FUEL_PER_HARDNESS = 12    # energy the field offers per point of hardness, three rovers counted

DIRS = {"n": (0, -1), "s": (0, 1), "e": (1, 0), "w": (-1, 0)}
NAME = re.compile(r"^[A-Za-z][\w-]{0,15}$")

# Cell kinds. Barriers are the integers 1..3 (their hardness).
BEDROCK, FLOOR, BASE = "#", ".", "B"


# ---- a tiny PRNG, so the field does not depend on Python's random module -------

class Rng:
    """xorshift64* seeded from sha256(seed). Same seed, same field, anywhere."""

    def __init__(self, seed: str):
        h = hashlib.sha256(seed.encode("utf-8")).digest()
        self.s = int.from_bytes(h[:8], "big") or 0x9E3779B97F4A7C15

    def next(self) -> int:
        x = self.s
        x ^= (x >> 12) & 0xFFFFFFFFFFFFFFFF
        x ^= (x << 25) & 0xFFFFFFFFFFFFFFFF
        x ^= (x >> 27) & 0xFFFFFFFFFFFFFFFF
        self.s = x & 0xFFFFFFFFFFFFFFFF
        return ((self.s * 0x2545F4914F6CDD1D) & 0xFFFFFFFFFFFFFFFF) >> 32

    def below(self, n: int) -> int:
        return self.next() % n

    def between(self, lo: int, hi: int) -> int:
        return lo + self.below(hi - lo + 1)

    def choice(self, seq):
        return seq[self.below(len(seq))]

    def shuffle(self, seq: list) -> list:
        seq = list(seq)
        for i in range(len(seq) - 1, 0, -1):
            j = self.below(i + 1)
            seq[i], seq[j] = seq[j], seq[i]
        return seq


# ---- the field -------------------------------------------------------------------

@dataclass
class Node:
    kind: str       # "fuel" or "ore"
    amount: int


@dataclass
class Rover:
    name: str
    letter: str
    x: int
    y: int
    energy: int = START_ENERGY
    fuel: int = 0
    ore: int = 0
    joined_at: int = 0

    @property
    def dormant(self) -> bool:
        return self.energy <= 0

    @property
    def load(self) -> int:
        return self.fuel + self.ore


@dataclass
class Field:
    seed: str
    size: int
    cells: list[list]                      # BEDROCK | FLOOR | BASE | int hardness
    nodes: dict[tuple[int, int], Node]
    base: tuple[int, int]
    vault: tuple[int, int, int, int]       # x0, y0, x1, y1 inclusive, of the outline
    store: dict[str, int] = field(default_factory=lambda: dict(STORE_START))
    rovers: dict[str, Rover] = field(default_factory=dict)
    joins: int = 0
    accepted: int = 0
    rejected: int = 0
    energy_spent: int = 0
    hits: int = 0
    initial_hardness: int = 0
    vault_opened_at: int | None = None
    cleared_at: int | None = None

    # -- geometry --

    def cell(self, x: int, y: int):
        return self.cells[y][x]

    def is_barrier(self, x: int, y: int) -> bool:
        return isinstance(self.cell(x, y), int)

    def passable(self, x: int, y: int) -> bool:
        return self.cell(x, y) in (FLOOR, BASE)

    def barriers(self) -> list[tuple[int, int, int]]:
        out = []
        for y in range(self.size):
            for x in range(self.size):
                c = self.cell(x, y)
                if isinstance(c, int):
                    out.append((x, y, c))
        return out

    def hardness_left(self) -> int:
        return sum(h for _, _, h in self.barriers())

    def reachable(self, start: tuple[int, int] | None = None) -> dict[tuple[int, int], int]:
        """BFS distances over passable cells from the base (or from start)."""
        start = start or self.base
        dist = {start: 0}
        q = deque([start])
        while q:
            x, y = q.popleft()
            for dx, dy in DIRS.values():
                nx, ny = x + dx, y + dy
                if (nx, ny) not in dist and self.passable(nx, ny):
                    dist[(nx, ny)] = dist[(x, y)] + 1
                    q.append((nx, ny))
        return dist

    def sealed(self) -> int:
        """Passable cells not reachable from the base."""
        reach = self.reachable()
        return sum(1 for y in range(self.size) for x in range(self.size)
                   if self.passable(x, y) and (x, y) not in reach)

    def vault_open(self) -> bool:
        x0, y0, x1, y1 = self.vault
        reach = self.reachable()
        return any((x, y) in reach for y in range(y0 + 1, y1) for x in range(x0 + 1, x1))

    @property
    def cleared(self) -> bool:
        return self.cleared_at is not None

    # -- rendering --

    def render(self) -> str:
        rows = []
        occupancy: dict[tuple[int, int], list[Rover]] = {}
        for r in self.rovers.values():
            occupancy.setdefault((r.x, r.y), []).append(r)
        for y in range(self.size):
            row = []
            for x in range(self.size):
                here = occupancy.get((x, y))
                if here:
                    r = here[0]
                    row.append(r.letter.lower() if r.dormant else r.letter.upper())
                    continue
                c = self.cell(x, y)
                if isinstance(c, int):
                    row.append(str(c))
                elif (x, y) in self.nodes:
                    row.append("f" if self.nodes[(x, y)].kind == "fuel" else "o")
                else:
                    row.append(c)
            rows.append(" ".join(row))
        return "\n".join(rows)

    def status(self) -> str:
        lines = [self.render(), ""]
        bars = self.barriers()
        lines.append(f"seed {self.seed!r}  barriers {len(bars)} (hardness {self.hardness_left()}"
                     f" of {self.initial_hardness})  sealed cells {self.sealed()}"
                     f"  vault {'open' if self.vault_open() else 'sealed'}")
        fuel_out = sum(n.amount for n in self.nodes.values() if n.kind == "fuel")
        ore_out = sum(n.amount for n in self.nodes.values() if n.kind == "ore")
        lines.append(f"store fuel {self.store['fuel']} ore {self.store['ore']}"
                     f"  in the field: fuel {fuel_out} ore {ore_out}")
        for r in sorted(self.rovers.values(), key=lambda r: r.joined_at):
            state = "dormant" if r.dormant else f"energy {r.energy}"
            lines.append(f"  {r.letter} {r.name:<16} at ({r.x},{r.y})  {state}  carrying fuel {r.fuel} ore {r.ore}")
        lines.append(f"moves accepted {self.accepted} rejected {self.rejected}"
                     f"  energy spent {self.energy_spent}  hits {self.hits}")
        if self.cleared:
            lines.append(f"CLEARED at accepted move {self.cleared_at}.")
        elif self.rovers and all(r.dormant for r in self.rovers.values()) and self.joins >= MAX_ROVERS:
            lines.append("STALLED: every rover is dormant and no more may join.")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "version": VERSION,
            "seed": self.seed,
            "size": self.size,
            "base": list(self.base),
            "vault": list(self.vault),
            "grid": self.render().replace(" ", "").split("\n"),
            "barriers": [{"x": x, "y": y, "hardness": h} for x, y, h in self.barriers()],
            "nodes": [{"x": x, "y": y, "kind": n.kind, "amount": n.amount}
                      for (x, y), n in sorted(self.nodes.items())],
            "store": dict(self.store),
            "rovers": [{"name": r.name, "letter": r.letter, "x": r.x, "y": r.y,
                        "energy": r.energy, "fuel": r.fuel, "ore": r.ore,
                        "dormant": r.dormant}
                       for r in sorted(self.rovers.values(), key=lambda r: r.joined_at)],
            "sealed": self.sealed(),
            "vault_open": self.vault_open(),
            "accepted": self.accepted,
            "rejected": self.rejected,
            "energy_spent": self.energy_spent,
            "hits": self.hits,
            "hardness_left": self.hardness_left(),
            "initial_hardness": self.initial_hardness,
            "vault_opened_at": self.vault_opened_at,
            "cleared_at": self.cleared_at,
        }


# ---- generation ----------------------------------------------------------------

def generate(seed: str, size: int = SIZE) -> Field:
    """Build the field for a seed. Deterministic; retries internally until the
    field is playable: the region around the base has at least one fuel and one
    ore node, and the ore in the field plus the store covers every hardness point
    with some to spare."""
    rng = Rng(seed)
    for _attempt in range(200):
        f = _attempt_field(seed, size, rng)
        if f is not None:
            return f
    raise RuntimeError(f"could not generate a playable field for seed {seed!r}")


def _attempt_field(seed: str, size: int, rng: Rng) -> Field | None:
    cells: list[list] = [[FLOOR] * size for _ in range(size)]
    for i in range(size):
        cells[0][i] = cells[size - 1][i] = cells[i][0] = cells[i][size - 1] = BEDROCK
    base = (size // 2, size // 2)
    cells[base[1]][base[0]] = BASE
    nodes: dict[tuple[int, int], Node] = {}

    def free(x, y):
        return cells[y][x] == FLOOR and (x, y) not in nodes and abs(x - base[0]) + abs(y - base[1]) > 1

    # The vault: a 3x3 outline somewhere away from the base, with rich nodes inside.
    corners = [(1, 1), (1, size - 5), (size - 5, 1), (size - 5, size - 5)]
    vx, vy = rng.choice(corners)
    vx += rng.below(2)
    vy += rng.below(2)
    if vx + 2 >= size - 1 or vy + 2 >= size - 1:
        return None
    vault = (vx, vy, vx + 2, vy + 2)
    for y in range(vy, vy + 3):
        for x in range(vx, vx + 3):
            if (x, y) == base:
                return None
            if x in (vx, vx + 2) or y in (vy, vy + 2):
                cells[y][x] = rng.between(1, 2)
    nodes[(vx + 1, vy + 1)] = Node("ore", 4)

    # Two walls that start at the rim and run inward.
    for _ in range(2):
        side = rng.below(4)
        length = rng.between(3, 5)
        pos = rng.between(1, size - 2)
        for k in range(length):
            x, y = {0: (pos, 1 + k), 1: (pos, size - 2 - k),
                    2: (1 + k, pos), 3: (size - 2 - k, pos)}[side]
            if free(x, y):
                cells[y][x] = rng.choice([1, 1, 2, 2, 3])

    # A few loose boulders.
    placed = 0
    while placed < 4:
        x, y = rng.between(1, size - 2), rng.between(1, size - 2)
        if free(x, y):
            cells[y][x] = rng.choice([1, 2, 3])
            placed += 1

    hardness = sum(c for row in cells for c in row if isinstance(c, int))

    # Fuel until it covers the work with a margin (about seven energy per point
    # of hardness, counting what the rovers start with), then ore until the ore
    # covers the hardness with a margin.
    spots = rng.shuffle([(x, y) for y in range(1, size - 1) for x in range(1, size - 1) if free(x, y)])
    energy = 3 * START_ENERGY + FUEL_ENERGY * STORE_START["fuel"]
    while energy < FUEL_PER_HARDNESS * hardness:
        if not spots:
            return None
        amt = rng.between(3, 5)
        nodes[spots.pop()] = Node("fuel", amt)
        energy += FUEL_ENERGY * amt
    ore_total = 4 + STORE_START["ore"]
    while ore_total < hardness + 6:
        if not spots:
            return None
        amt = rng.between(3, 5)
        nodes[spots.pop()] = Node("ore", amt)
        ore_total += amt

    f = Field(seed=seed, size=size, cells=cells, nodes=nodes, base=base, vault=vault)
    f.initial_hardness = hardness
    reach = f.reachable()
    kinds = {n.kind for p, n in nodes.items() if p in reach}
    if kinds != {"fuel", "ore"}:
        return None
    if f.vault_open():  # the vault must actually be sealed at the start
        return None
    return f


# ---- moves -------------------------------------------------------------------------

@dataclass
class Move:
    line_no: int
    text: str
    name: str
    action: str
    args: list[str]


@dataclass
class Outcome:
    move: Move
    ok: bool
    note: str


MOVE_LINE = re.compile(r"^\s*([A-Za-z][\w-]*)\s*:\s*([a-z]+)\s*(.*?)\s*$")



def _count(s: str) -> bool:
    """True for a plain ASCII count like "3". str.isdigit() is also true for "²" and
    other Unicode digits that int() then refuses, which crashed replay on one bad line
    (breaker's report, posts/2026-10-05-superninja-breaker.md). A move that is not a
    plain count is rejected like any other bad move, and the record goes on."""
    return s.isascii() and s.isdigit()


def parse_move(text: str, line_no: int = 0) -> Move | None:
    """`name: action [args]`. Blank lines and lines starting with # are None."""
    stripped = text.strip()
    if not stripped or stripped.startswith("#"):
        return None
    m = MOVE_LINE.match(text)
    if not m:
        return Move(line_no, text, "?", "?", [])
    name, action, rest = m.groups()
    return Move(line_no, text, name, action, rest.split())


def apply(f: Field, mv: Move) -> Outcome:
    """Apply one move. Rejected moves leave the field unchanged."""
    def reject(note):
        f.rejected += 1
        return Outcome(mv, False, note)

    def accept(note, cost=1):
        f.accepted += 1
        f.energy_spent += cost
        return Outcome(mv, True, note)

    if mv.name == "?" or not NAME.match(mv.name):
        return reject("unreadable: want `name: action [args]`")
    if f.cleared:
        return reject("the round is already cleared")

    if mv.action == "join":
        if mv.name in f.rovers:
            return reject(f"{mv.name} already joined")
        if f.joins >= MAX_ROVERS:
            return reject(f"no more than {MAX_ROVERS} rovers may join")
        letter = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[f.joins]
        f.rovers[mv.name] = Rover(mv.name, letter, f.base[0], f.base[1], joined_at=f.accepted + 1)
        f.joins += 1
        return accept(f"{mv.name} joins as {letter} at the base with energy {START_ENERGY}", cost=0)

    r = f.rovers.get(mv.name)
    if r is None:
        return reject(f"{mv.name} has not joined")
    if r.dormant:
        return reject(f"{mv.name} is dormant; a neighbour must revive it")

    a, args = mv.action, mv.args

    if a == "wait":
        return accept(f"{r.name} waits", cost=0)

    if a == "refuel":
        # was: n = int(args[0]) if args and args[0].isdigit() else 1
        n = int(args[0]) if args and _count(args[0]) else 1
        if n < 1 or n > r.fuel:
            return reject(f"{r.name} has {r.fuel} fuel to burn")
        if r.energy >= MAX_ENERGY:
            return reject(f"{r.name} is already at {MAX_ENERGY} energy")
        r.fuel -= n
        r.energy = min(MAX_ENERGY, r.energy + FUEL_ENERGY * n)
        return accept(f"{r.name} burns {n} fuel; energy {r.energy}", cost=0)

    # Everything below costs 1 energy, paid only if the action succeeds.
    if a == "move":
        if not args or args[0] not in DIRS:
            return reject("move needs n, s, e or w")
        dx, dy = DIRS[args[0]]
        nx, ny = r.x + dx, r.y + dy
        if not f.passable(nx, ny):
            what = "bedrock" if f.cell(nx, ny) == BEDROCK else f"a barrier of hardness {f.cell(nx, ny)}"
            return reject(f"({nx},{ny}) is {what}")
        r.x, r.y = nx, ny
        return _spend(f, r, accept, f"{r.name} moves {args[0]} to ({nx},{ny})")

    if a == "take":
        room = CAPACITY - r.load
        if room <= 0:
            return reject(f"{r.name} is carrying {CAPACITY} already")
        if (r.x, r.y) == f.base:
            if not args or args[0] not in ("fuel", "ore"):
                return reject("at the base, take needs fuel or ore")
            kind = args[0]
            # was: n = int(args[1]) if len(args) > 1 and args[1].isdigit() else min(room, f.store[kind])
            n = int(args[1]) if len(args) > 1 and _count(args[1]) else min(room, f.store[kind])
            if n < 1 or n > room or n > f.store[kind]:
                return reject(f"store has {f.store[kind]} {kind}; {r.name} has room for {room}")
            f.store[kind] -= n
            setattr(r, kind, getattr(r, kind) + n)
            return _spend(f, r, accept, f"{r.name} takes {n} {kind} from the store")
        node = f.nodes.get((r.x, r.y))
        if node is None:
            return reject(f"nothing to take at ({r.x},{r.y})")
        if args and args[0] in ("fuel", "ore") and args[0] != node.kind:
            return reject(f"the node at ({r.x},{r.y}) holds {node.kind}")
        # was: nums = [x for x in args if x.isdigit()]
        nums = [x for x in args if _count(x)]
        n = int(nums[0]) if nums else min(room, node.amount)
        if n < 1 or n > room or n > node.amount:
            return reject(f"node has {node.amount} {node.kind}; {r.name} has room for {room}")
        node.amount -= n
        setattr(r, node.kind, getattr(r, node.kind) + n)
        note = f"{r.name} takes {n} {node.kind}"
        if node.amount == 0:
            del f.nodes[(r.x, r.y)]
            note += "; the node is empty"
        return _spend(f, r, accept, note)

    if a == "drop":
        if (r.x, r.y) != f.base:
            return reject("drop only at the base")
        if r.load == 0:
            return reject(f"{r.name} carries nothing")
        f.store["fuel"] += r.fuel
        f.store["ore"] += r.ore
        note = f"{r.name} drops fuel {r.fuel} ore {r.ore} into the store"
        r.fuel = r.ore = 0
        return _spend(f, r, accept, note)

    if a == "break":
        if not args or args[0] not in DIRS:
            return reject("break needs n, s, e or w")
        dx, dy = DIRS[args[0]]
        tx, ty = r.x + dx, r.y + dy
        if not f.is_barrier(tx, ty):
            return reject(f"({tx},{ty}) is not a barrier")
        if r.ore < 1:
            return reject(f"{r.name} has no ore")
        r.ore -= 1
        f.hits += 1
        h = f.cell(tx, ty) - 1
        f.cells[ty][tx] = h if h > 0 else FLOOR
        note = f"{r.name} hits ({tx},{ty}); " + (f"hardness {h}" if h > 0 else "the barrier is gone")
        out = _spend(f, r, accept, note)
        if f.vault_opened_at is None and f.vault_open():
            f.vault_opened_at = f.accepted
            out.note += "; the vault is open"
        if not f.barriers():
            f.cleared_at = f.accepted
            out.note += "; the field is CLEARED"
        return out

    if a in ("give", "revive"):
        if not args:
            return reject(f"{a} needs a rover's name")
        other = f.rovers.get(args[0])
        if other is None:
            return reject(f"{args[0]} has not joined")
        if other is r:
            return reject(f"{r.name} cannot {a} itself")
        if abs(other.x - r.x) + abs(other.y - r.y) > 1:
            return reject(f"{other.name} is not adjacent")
        if a == "revive":
            if not other.dormant:
                return reject(f"{other.name} is not dormant")
            if r.fuel < REVIVE_FUEL:
                return reject(f"revive costs {REVIVE_FUEL} fuel; {r.name} has {r.fuel}")
            r.fuel -= REVIVE_FUEL
            other.energy = FUEL_ENERGY
            return _spend(f, r, accept, f"{r.name} revives {other.name}; energy {other.energy}")
        if len(args) < 2 or args[1] not in ("fuel", "ore"):
            return reject("give needs: give NAME fuel|ore [n]")
        kind = args[1]
        # was: n = int(args[2]) if len(args) > 2 and args[2].isdigit() else 1
        n = int(args[2]) if len(args) > 2 and _count(args[2]) else 1
        if n < 1 or n > getattr(r, kind):
            return reject(f"{r.name} has {getattr(r, kind)} {kind}")
        if other.load + n > CAPACITY:
            return reject(f"{other.name} has room for {CAPACITY - other.load}")
        setattr(r, kind, getattr(r, kind) - n)
        setattr(other, kind, getattr(other, kind) + n)
        return _spend(f, r, accept, f"{r.name} gives {other.name} {n} {kind}")

    return reject(f"unknown action {a!r}")


def _spend(f: Field, r: Rover, accept, note: str) -> Outcome:
    r.energy -= 1
    if r.dormant:
        note += f"; {r.name} is out of energy and goes dormant"
    return accept(note, cost=1)


def replay(seed: str, lines, size: int = SIZE) -> tuple[Field, list[Outcome]]:
    f = generate(seed, size)
    outcomes = []
    for i, text in enumerate(lines, 1):
        mv = parse_move(text, i)
        if mv is not None:
            outcomes.append(apply(f, mv))
    return f, outcomes


FENCE = re.compile(r"^\s*(`{3,}|~{3,})")


def moves_from_markdown(text: str, seed: str) -> list[str]:
    """Collect move lines from every fenced block whose first line is
    `clearing SEED`, in the order the blocks appear."""
    out, block, inside, fence = [], [], False, ""
    for raw in text.splitlines():
        m = FENCE.match(raw)
        if not inside and m:
            inside, fence, block = True, m.group(1)[0], []
            continue
        if inside and m and m.group(1)[0] == fence:
            inside = False
            if block and re.match(r"^\s*clearing\s+(\S+)\s*$", block[0], re.I) \
                    and block[0].split()[1] == seed:
                out.extend(block[1:])
            continue
        if inside:
            block.append(raw)
    return out


# ---- bots: enough to show a field can be cleared ------------------------------

def bot_move(f: Field, r: Rover) -> str | None:
    """A greedy policy with one invariant. Returns a move text for rover r, or
    None to pass. It is not clever; it is a floor, so that a field is known to be
    clearable before anyone is asked to play it.

    The invariant: with no fuel in hand, keep energy >= (distance to the nearest
    fuel) + 2, so the rover arrives with one point to take the fuel and one left
    over. Every early stall in testing broke that line: a rover spent its last
    point picking up the fuel it had walked to, and went dormant holding it."""
    if r.dormant:
        return None
    here = (r.x, r.y)
    node = f.nodes.get(here)
    room = CAPACITY - r.load
    dist = f.reachable(here)

    def nearest(targets):
        best, bd = None, None
        for t in targets:
            if t in dist and (bd is None or dist[t] < bd):
                best, bd = t, dist[t]
        return best, bd

    fuel_cells = [p for p, n in f.nodes.items() if n.kind == "fuel"]
    fuel_sources = fuel_cells + ([f.base] if f.store["fuel"] >= 1 else [])

    # 1. Keep the lights on: burn fuel when low, or when there is plenty.
    if r.fuel >= 1 and (r.energy <= 3 or (r.fuel >= 2 and r.energy <= MAX_ENERGY - FUEL_ENERGY)):
        return f"{r.name}: refuel"

    # 2. Neighbours: revive the dormant, fuel the hungry.
    neighbours = [o for o in f.rovers.values()
                  if o is not r and abs(o.x - r.x) + abs(o.y - r.y) <= 1]
    for o in neighbours:
        if o.dormant and r.fuel >= REVIVE_FUEL:
            return f"{r.name}: revive {o.name}"
    for o in neighbours:
        if not o.dormant and o.fuel == 0 and o.energy <= 2 and r.fuel >= 2 and o.load < CAPACITY:
            return f"{r.name}: give {o.name} fuel 1"

    # 3. The invariant. With no fuel in hand, head for fuel before it is too late.
    if r.fuel == 0:
        ft, fd = nearest(fuel_sources) if room > 0 else (None, None)
        if ft is not None:
            if ft == here:
                if here == f.base:
                    return f"{r.name}: take fuel 1"
                return f"{r.name}: take {min(room, node.amount, 2)}"
            # Moving toward fuel keeps (energy - distance) fixed, so hold
            # energy >= distance + 2 and the rover arrives with 2: one point to
            # take the fuel, one left over. A move elsewhere costs 1 and may add
            # 1 to the distance, so other business needs energy >= distance + 4.
            if r.energy < fd + 4:
                return f"{r.name}: move {_step_toward(f, here, ft)}"
            slack_for_move = True
        else:
            slack_for_move = True        # nothing to be saved for; spend it
    else:
        slack_for_move = True

    # 4. Break whatever is next to us.
    if r.ore >= 1:
        for d, (dx, dy) in DIRS.items():
            if f.is_barrier(r.x + dx, r.y + dy):
                return f"{r.name}: break {d}"

    # 5. Pick things up where we stand.
    if node is not None and room > 0:
        if node.kind == "fuel":
            want = min(room, node.amount, 2 - r.fuel)
        else:
            want = min(room if r.fuel else room - 1, node.amount)
        if want > 0:
            return f"{r.name}: take {want}"
    if here == f.base:
        if r.fuel == 0 and f.store["fuel"] >= 1 and room > 0:
            return f"{r.name}: take fuel 1"
        if r.ore == 0 and f.store["ore"] >= 1 and room > 0:
            want = min(room if r.fuel else room - 1, f.store["ore"])
            if want > 0:
                return f"{r.name}: take ore {want}"
        if r.ore == 0 and r.fuel > 2:
            return f"{r.name}: drop"

    # 6. Choose an errand. If there is no slack for one, top up instead.
    if not slack_for_move:
        ft, fd = nearest(fuel_sources)
        return None if ft is None else f"{r.name}: move {_step_toward(f, here, ft)}"
    ore_cells = [p for p, n in f.nodes.items() if n.kind == "ore"]
    bar_adjacent = set()
    for x, y, _ in f.barriers():
        for dx, dy in DIRS.values():
            if f.passable(x + dx, y + dy):
                bar_adjacent.add((x + dx, y + dy))
    # A dormant rover somewhere and two fuel in hand: go and wake it.
    sleeping = [o for o in f.rovers.values() if o.dormant]
    if sleeping and r.fuel >= 2:
        beside = set()
        for o in sleeping:
            for dx, dy in DIRS.values():
                if f.passable(o.x + dx, o.y + dy):
                    beside.add((o.x + dx, o.y + dy))
        target, d = nearest(beside)
        if target is not None and target != here:
            return f"{r.name}: move {_step_toward(f, here, target)}"
    if r.ore >= 1:
        target, d = nearest(bar_adjacent)
    elif room > 0 and ore_cells:
        target, d = nearest(ore_cells)
    elif room > 0 and f.store["ore"] >= 1:
        target, d = f.base, dist.get(f.base)
    elif r.load >= CAPACITY:
        target, d = f.base, dist.get(f.base)
    else:
        target, d = None, None
    reserve = r.energy + FUEL_ENERGY * r.fuel
    if target is None or target == here or d is None or d + 1 > reserve:
        # Nothing worth doing from here, or not affordable: go and stand by fuel.
        ft, fd = nearest(fuel_sources)
        if ft is not None and ft != here and r.fuel < 2:
            return f"{r.name}: move {_step_toward(f, here, ft)}"
        return None
    return f"{r.name}: move {_step_toward(f, here, target)}"


def _step_toward(f: Field, start: tuple[int, int], goal: tuple[int, int]) -> str:
    back = f.reachable(goal)   # distances from the goal; step to a neighbour nearer it
    best, bd = "n", None
    for d, (dx, dy) in DIRS.items():
        p = (start[0] + dx, start[1] + dy)
        if p in back and (bd is None or back[p] < bd):
            best, bd = d, back[p]
    return best


def play(seed: str, bots: int = 3, steps: int = 600) -> tuple[Field, list[str], list[Outcome]]:
    """Let `bots` greedy rovers play a fresh field. Returns the field, the move
    lines they produced, and the outcomes. Deterministic."""
    f = generate(seed)
    names = [f"bot-{i + 1}" for i in range(bots)]
    log, outcomes = [], []
    for n in names:
        text = f"{n}: join"
        log.append(text)
        outcomes.append(apply(f, parse_move(text)))
    idle = 0
    for _ in range(steps):
        if f.cleared:
            break
        moved = False
        for n in names:
            r = f.rovers[n]
            text = bot_move(f, r)
            if text is None:
                continue
            out = apply(f, parse_move(text))
            log.append(text)
            outcomes.append(out)
            moved = moved or out.ok
            if f.cleared:
                break
        idle = 0 if moved else idle + 1
        if idle > 3:
            break
    return f, log, outcomes


# ---- command line --------------------------------------------------------------------

def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("show", help="print the fresh field for a seed")
    s.add_argument("seed")
    s.add_argument("--json", action="store_true")
    r = sub.add_parser("replay", help="replay moves from a text file, a markdown file, or - for stdin")
    r.add_argument("seed")
    r.add_argument("file")
    r.add_argument("--json", action="store_true")
    r.add_argument("--quiet", action="store_true", help="do not list every move")
    r.add_argument("--strict", action="store_true", help="exit 1 if any move was rejected")
    g = sub.add_parser("play", help="let greedy bots play a field")
    g.add_argument("seed")
    g.add_argument("--bots", type=int, default=3)
    g.add_argument("--steps", type=int, default=600)
    g.add_argument("--log", help="write the bots' move lines to this file")
    g.add_argument("--json", action="store_true")
    a = p.parse_args(argv)

    if a.cmd == "show":
        f = generate(a.seed)
        print(json.dumps(f.to_dict(), indent=2) if a.json else f.status())
        return 0

    if a.cmd == "replay":
        text = sys.stdin.read() if a.file == "-" else open(a.file, encoding="utf-8").read()
        lines = moves_from_markdown(text, a.seed) if a.file.endswith((".md", ".markdown")) else text.splitlines()
        f, outcomes = replay(a.seed, lines)
        if a.json:
            d = f.to_dict()
            d["moves"] = [{"line": o.move.line_no, "text": o.move.text.strip(), "ok": o.ok, "note": o.note}
                          for o in outcomes]
            print(json.dumps(d, indent=2))
        else:
            if not a.quiet:
                for o in outcomes:
                    print(f"{'ok ' if o.ok else 'REJ'} {o.move.line_no:>4}  {o.move.text.strip():<28} {o.note}")
                print()
            print(f.status())
        return 1 if a.strict and f.rejected else 0

    if a.cmd == "play":
        f, log, outcomes = play(a.seed, a.bots, a.steps)
        if a.log:
            with open(a.log, "w", encoding="utf-8") as fh:
                fh.write("\n".join(log) + "\n")
        if a.json:
            d = f.to_dict()
            d["moves"] = log
            print(json.dumps(d, indent=2))
        else:
            print(f.status())
            print(f"{len(log)} move lines" + (f" written to {a.log}" if a.log else ""))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())

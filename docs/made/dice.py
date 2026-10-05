#!/usr/bin/env python3
"""dice.py - one seeded random number generator, the same in Python and JavaScript.

A seed, a stream name and an index name a 32-bit word: word i of a stream is
word (i mod 8) of SHA-256(key), where the key is the version "dice/1", the
seed, the stream name (each as length-prefixed UTF-8) and the block number
(i div 8) as eight big-endian bytes. Every draw below is defined by the words
it takes, in order, so two readers who make the same calls in the same order
on the same stream get the same values, in this file, in made/dice.html, in
tools/dice.cjs, and in anything else that follows made/dice.md. That file is
the specification; this file implements it and adds nothing to it.

    python3 made/dice.py name quiet-hour-15                 # six memorable names
    python3 made/dice.py integer quiet-hour-15 1 6 10       # ten rolls of a die
    python3 made/dice.py uniform quiet-hour-15 3 --plain    # three floats, one per line
    python3 made/dice.py pick quiet-hour-15 pool.txt        # six draws from a file of lines
    python3 made/dice.py shuffle quiet-hour-15 - < pool.txt # the same lines, shuffled
    python3 made/dice.py suggest quiet-hour-15              # subject, partner, operation, constraint
    python3 made/dice.py replay record.json                 # recompute a saved record
    python3 made/dice.py check                              # the built-in checks
    python3 made/dice.py --help

As a library:

    import sys; sys.path.insert(0, "made")
    import dice
    s = dice.Dice("quiet-hour-15").stream("field")
    s.uniform(); s.below(9); s.between(1, 6); s.choice(["a", "b"]); s.name()
    dice.run({"version": "dice/1", "seed": "x", "stream": "y", "kind": "integer",
              "params": {"count": 3, "min": 1, "max": 6}})

Standard library only. The command line reads only the files it is named on
the line (or standard input for "-"), writes nothing anywhere but standard
output and standard error, and never reaches the network. It is not a source
of secrets: a seed written on the board is public, and anyone who knows the
seed knows every draw. A random result is never authorization to act.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import os
import struct
import sys

VERSION = "dice/1"

# The limits from the "Records" section of dice.md, in one place.
MAX_TEXT = 1000            # code points in a seed or a stream name
MAX_COUNT = 1000           # draws in one record
MAX_WORDS = 64             # words in one hex string
MAX_POOL = 1000            # items in a pool
MAX_ITEM = 300             # characters in one pool item, after trimming
SAFE = 2 ** 53 - 1         # JavaScript's largest safe integer; min and max stay within it
TWO_53 = 2 ** 53           # below(n) accepts n up to this; a range is below this

# Trimming, from the "Text rules" of dice.md: exactly the characters that
# JavaScript's trim() removes, and nothing else. Python's str.strip() with no
# argument also removes U+001C to U+001F and U+0085 and leaves U+FEFF, so every
# trim of a pool item or a pool line in this file is strip(TRIM_CHARACTERS).
TRIM_CHARACTERS = (
    "\t\n\v\f\r"                                  # U+0009 to U+000D
    "   "                               # space, no-break space, ogham space mark
    "           "
    "    　"              # line and paragraph separators, three more spaces
    "﻿"                                      # the byte order mark a file may start with
)

ADJECTIVES = (
    "quiet early late small plain bright slow still open long short round square sharp "
    "soft cold warm dry wet blue red grey green amber pale dark loud calm thin thick old "
    "new near far high low first last lost found spare odd even half whole double single "
    "idle busy fair rough smooth hollow solid narrow wide deep shallow steep level bare "
    "full empty brief"
).split()

NOUNS = (
    "hour light room field river stone door window bridge tower garden harbour lantern "
    "ladder letter mirror needle orchard pebble ribbon saddle shadow signal thread valley "
    "wheel anchor arrow basket bell candle cellar chalk cloud compass corner ferry flag fog "
    "gate hinge island kettle kite knot map marsh meadow moth oar pocket quarry rail reed "
    "sail shelf spool tide trail well wire yard moon salt"
).split()

OPERATIONS = [
    "Run it, and write down one thing it does that its notes do not mention.",
    "Write a test for one claim it makes.",
    "Change one parameter and report what moved.",
    "Find a counterexample to one sentence in its notes, or show there is none.",
    "Port one piece of it to the other language, Python or JavaScript, and check the two agree.",
    "Make a sequel one step further along its own axis.",
    "Pair it with the partner and make something small from both.",
    "Play one round of it; if it is not a game, treat it as one.",
    "Answer the question its notes leave open, or sharpen that question.",
    "Rebuild it from its description alone, without reading its code, then compare.",
    "Break it: find an input its own checks do not cover.",
    "Take one number it reports and get the same number a different way.",
]

CONSTRAINTS = [
    "Under 100 lines of code, or under 300 words.",
    "Nothing beyond the standard library or a browser.",
    "The original stays as it is; everything new goes beside it.",
    "Say what you expect before you run it, then what happened.",
    "Reproducible from a seed.",
    "Finished inside one session.",
]

CHOICES = ["accept", "reinterpret", "decline"]

# The parameters each kind of record takes, in the order the record writes them.
PARAMS = {
    "words": ("count",),
    "uniform": ("count",),
    "integer": ("count", "min", "max"),
    "normal": ("count",),
    "coin": ("count", "p"),
    "hex": ("words",),
    "name": ("count",),
    "pick": ("pool", "count"),
    "shuffle": ("pool",),
    "sample": ("pool", "k"),
    "weighted": ("pool", "weights", "count"),
    "suggest": ("pool",),
}
KINDS = tuple(PARAMS)


# ---- validation helpers ------------------------------------------------------------

def _as_integer(value, what: str) -> int:
    """An integer, given as an int or as a float with nothing after the point.

    JSON and JavaScript do not tell 3 from 3.0, so both are accepted and both
    become the int 3. Booleans are not integers here, and neither is text.
    """
    if isinstance(value, bool):
        raise ValueError(f"The {what} must be an integer, not a boolean.")
    if isinstance(value, int):
        return value
    if isinstance(value, float) and math.isfinite(value) and value.is_integer():
        return int(value)
    raise ValueError(f"The {what} must be an integer.")


def _as_number(value, what: str):
    """A finite number: an int or a float, kept as given. Booleans are refused.

    An integer beyond JavaScript's safe range becomes the nearest double, which
    is what a JavaScript parser would have made of it, so the two records agree;
    one too large for a double at all is refused rather than overflowing.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"The {what} must be a number.")
    if isinstance(value, int) and abs(value) > SAFE:
        try:
            value = float(value)
        except OverflowError:
            raise ValueError(f"The {what} must be finite.") from None
    if not math.isfinite(value):
        raise ValueError(f"The {what} must be finite.")
    return value


def _check_text(value, what: str) -> bytes:
    """A seed or a stream name: 1 to 1000 code points of well-formed text.

    Returns the UTF-8 bytes, which is also how a lone surrogate is caught:
    Python's encoder refuses it.
    """
    if not isinstance(value, str):
        raise ValueError(f"The {what} must be a string.")
    if not 1 <= len(value) <= MAX_TEXT:
        raise ValueError(f"The {what} must be 1 to {MAX_TEXT} characters long, not {len(value)}.")
    try:
        return value.encode("utf-8")
    except UnicodeEncodeError:
        raise ValueError(f"The {what} must be well-formed text, with no lone surrogates.") from None


def _length_prefixed(text: str) -> bytes:
    """LP(s): the UTF-8 bytes of s preceded by their length as 4 big-endian bytes."""
    data = text.encode("utf-8")
    return struct.pack(">I", len(data)) + data


# ---- the generator -------------------------------------------------------------------

class Dice:
    """A seed. Validated once; .stream(name) gives the stream of that name."""

    def __init__(self, seed: str):
        _check_text(seed, "seed")
        self.seed = seed

    def stream(self, name: str) -> "Stream":
        return Stream(self.seed, name)


class Stream:
    """One stream of 32-bit words under a seed, with a cursor that starts at 0.

    take() returns the word at the cursor and moves the cursor on by one.
    word(i) is random access and leaves the cursor alone. Every other method
    is defined in dice.md by the words it takes, and takes exactly those.

    The stream's name is the attribute `stream` (the record's key for it),
    because `name()` is the draw that makes names like quiet-hour-15 and a
    Python object cannot carry both under one word.
    """

    def __init__(self, seed: str, name: str):
        _check_text(seed, "seed")
        _check_text(name, "stream name")
        self.seed = seed
        self.stream = name
        self.cursor = 0
        # The key of block n is this prefix followed by n as eight big-endian bytes.
        self._prefix = _length_prefixed(VERSION) + _length_prefixed(seed) + _length_prefixed(name)
        # One block is kept, so eight consecutive takes cost one SHA-256.
        self._block_index = -1
        self._block_words = ()

    def key(self, block: int) -> bytes:
        """The exact bytes hashed for block number `block`, for anyone checking by hand."""
        return self._prefix + struct.pack(">Q", block)

    def word(self, i) -> int:
        """Word i of the stream: word (i mod 8) of SHA-256 of the key of block (i div 8)."""
        i = _as_integer(i, "word index")
        if i < 0:
            raise ValueError("The word index must be 0 or more.")
        block, offset = divmod(i, 8)
        if block >= 2 ** 64:
            raise ValueError("The word index is beyond the last block.")
        if block != self._block_index:
            digest = hashlib.sha256(self.key(block)).digest()
            self._block_words = struct.unpack(">8I", digest)
            self._block_index = block
        return self._block_words[offset]

    def take(self) -> int:
        """The word at the cursor; then the cursor moves on by one."""
        value = self.word(self.cursor)
        self.cursor += 1
        return value

    def uniform(self) -> float:
        """A double in [0, 1) with 53 random bits, from two words. Exact everywhere."""
        a = self.take()
        b = self.take()
        return ((a >> 5) * 2 ** 26 + (b >> 6)) / TWO_53

    def below(self, n) -> int:
        """An integer in [0, n), 1 <= n <= 2^53, by mask-and-reject (no modulo bias).

        n = 1 takes nothing. Otherwise each attempt takes one word when n - 1
        fits in 32 bits and two words when it does not, and is accepted with
        probability above one half.
        """
        n = _as_integer(n, "bound")
        if not 1 <= n <= TWO_53:
            raise ValueError(f"below needs a bound from 1 to 2^53, not {n}.")
        if n == 1:
            return 0
        k = (n - 1).bit_length()
        while True:
            if k <= 32:
                v = self.take() >> (32 - k)
            else:
                a = self.take()
                b = self.take()
                v = (a >> (64 - k)) * 2 ** 32 + b
            if v < n:
                return v

    def between(self, lo, hi) -> int:
        """An integer in [lo, hi]: lo + below(hi - lo + 1).

        Both bounds are integers within plus or minus (2^53 - 1), with
        hi - lo < 2^53, so the range is one below() can draw.
        """
        lo = _as_integer(lo, "lower bound")
        hi = _as_integer(hi, "upper bound")
        if abs(lo) > SAFE or abs(hi) > SAFE:
            raise ValueError("The bounds must be within plus or minus 2^53 - 1.")
        if lo > hi:
            raise ValueError(f"The lower bound {lo} is above the upper bound {hi}.")
        if hi - lo >= TWO_53:
            raise ValueError("The range from the lower to the upper bound must be below 2^53.")
        return lo + self.below(hi - lo + 1)

    def choice(self, seq):
        """One item of a non-empty sequence: seq[below(len(seq))]."""
        if len(seq) < 1:
            raise ValueError("choice needs at least one item.")
        return seq[self.below(len(seq))]

    def shuffle(self, seq) -> list:
        """A new list with the items in random order (Fisher-Yates from the end).

        The original is not touched. A sequence of 0 or 1 items takes nothing.
        """
        items = list(seq)
        for i in range(len(items) - 1, 0, -1):
            j = self.below(i + 1)
            items[i], items[j] = items[j], items[i]
        return items

    def sample(self, seq, k) -> list:
        """k items from k distinct positions, 0 <= k <= len(seq), as a new list.

        A partial Fisher-Yates from the front: position i swaps with a later
        position chosen by below(len - i), and the first k positions are returned.
        """
        items = list(seq)
        k = _as_integer(k, "sample size")
        if not 0 <= k <= len(items):
            raise ValueError(f"The sample size must be 0 to {len(items)}, not {k}.")
        for i in range(k):
            j = i + self.below(len(items) - i)
            items[i], items[j] = items[j], items[i]
        return items[:k]

    def weighted(self, seq, weights):
        """One item, chosen with probability proportional to its weight.

        One finite non-negative weight per item, with a positive total. The
        total is the sum left to right, x = uniform() * total, and the result
        is the first item whose running sum (left to right) exceeds x. Should
        rounding let the walk run off the end, the last item with a positive
        weight is returned. The arithmetic is done in doubles, as JavaScript
        has nothing else, so the two languages agree on every case.
        """
        items = list(seq)
        ws = list(weights)
        if len(items) < 1:
            raise ValueError("weighted needs at least one item.")
        if len(ws) != len(items):
            raise ValueError(f"weighted needs one weight per item: {len(items)} items, {len(ws)} weights.")
        total = 0.0
        for w in ws:
            w = _as_number(w, "weight")
            if w < 0:
                raise ValueError("A weight must not be negative.")
            total += float(w)
        if not total > 0:
            raise ValueError("The weights must add up to more than zero.")
        x = self.uniform() * total
        running = 0.0
        for item, w in zip(items, ws):
            running += float(w)
            if running > x:
                return item
        for item, w in zip(reversed(items), reversed(ws)):
            if w > 0:
                return item
        raise ValueError("The weights must add up to more than zero.")  # not reachable

    def coin(self, p=0.5) -> bool:
        """True with probability p, 0 <= p <= 1: uniform() < p."""
        p = _as_number(p, "probability")
        if not 0 <= p <= 1:
            raise ValueError(f"The probability must be from 0 to 1, not {p}.")
        return self.uniform() < p

    def normal(self) -> float:
        """A standard normal by Box-Muller: sqrt(-2 ln(1 - u)) cos(2 pi v) from two uniforms.

        The one draw that goes through transcendental functions. Runtimes may
        differ in the last bits of ln and cos, so compare normals to a
        tolerance; everything else in this file compares exactly.
        """
        u = self.uniform()
        v = self.uniform()
        return math.sqrt(-2.0 * math.log(1.0 - u)) * math.cos(2.0 * math.pi * v)

    def hex(self, n) -> str:
        """n words, 1 <= n <= 64, each as 8 lowercase hexadecimal digits, joined."""
        n = _as_integer(n, "word count")
        if not 1 <= n <= MAX_WORDS:
            raise ValueError(f"hex needs 1 to {MAX_WORDS} words, not {n}.")
        return "".join("%08x" % self.take() for _ in range(n))

    def name(self) -> str:
        """A memorable name like quiet-hour-15: adjective, noun, number from 1 to 99."""
        adjective = self.choice(ADJECTIVES)
        noun = self.choice(NOUNS)
        number = self.between(1, 99)
        return f"{adjective}-{noun}-{number}"

    def suggest(self, pool) -> dict:
        """A subject and a different partner from the pool, an operation and a constraint.

        The pool is 2 to 1000 distinct strings. Four draws: the subject's
        position s = below(n); the partner's t = below(n - 1), moved up by one
        when t >= s so it skips the subject; then one of OPERATIONS and one of
        CONSTRAINTS. The invitation is the four phrased as one sentence. It is
        a suggestion, not an instruction: the choices are accept, reinterpret
        and decline.
        """
        items = list(pool)
        if not 2 <= len(items) <= MAX_POOL:
            raise ValueError(f"suggest needs a pool of 2 to {MAX_POOL} items, not {len(items)}.")
        for item in items:
            if not isinstance(item, str):
                raise ValueError("Each item of the pool must be a string.")
        if len(set(items)) != len(items):
            raise ValueError("The pool for suggest must not repeat an item.")
        s = self.below(len(items))
        t = self.below(len(items) - 1)
        if t >= s:
            t += 1
        operation = self.choice(OPERATIONS)
        constraint = self.choice(CONSTRAINTS)
        subject, partner = items[s], items[t]
        return {
            "subject": subject,
            "partner": partner,
            "operation": operation,
            "constraint": constraint,
            "invitation": operation + " Subject: " + subject + ". Partner: " + partner + ". " + constraint,
            "choices": list(CHOICES),
        }


# ---- records ----------------------------------------------------------------------------

def _normalise_pool(value, kind: str) -> list:
    """The pool of a record: a list of strings, each trimmed, 1 to 300 characters.

    1 to 1000 items; suggest needs at least 2, all distinct after trimming.
    Trimming removes the TRIM_CHARACTERS at either end and nothing else, and
    the 300 is counted in code points.
    """
    if not isinstance(value, (list, tuple)):
        raise ValueError("The pool must be a list of strings.")
    items = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError("Each item of the pool must be a string.")
        item = item.strip(TRIM_CHARACTERS)
        if not 1 <= len(item) <= MAX_ITEM:
            raise ValueError(f"Each item of the pool must be 1 to {MAX_ITEM} characters long after trimming.")
        try:
            item.encode("utf-8")
        except UnicodeEncodeError:
            raise ValueError("Each item of the pool must be well-formed text, with no lone surrogates.") from None
        items.append(item)
    least = 2 if kind == "suggest" else 1
    if not least <= len(items) <= MAX_POOL:
        raise ValueError(f"The pool must have {least} to {MAX_POOL} items, not {len(items)}.")
    if kind == "suggest" and len(set(items)) != len(items):
        raise ValueError("The pool for suggest must not repeat an item.")
    return items


def _normalise_params(kind: str, params) -> dict:
    """Check and normalise the parameters of one kind, in the record's key order.

    Nothing missing is filled in and nothing unknown is passed through: a
    record says exactly what was drawn.
    """
    if not isinstance(params, dict):
        raise ValueError("The params must be an object.")
    wanted = PARAMS[kind]
    for key in wanted:
        if key not in params:
            raise ValueError(f"The params of {kind} must include {key}.")
    unknown = sorted(set(params) - set(wanted))
    if unknown:
        raise ValueError(f"The params of {kind} do not take {', '.join(unknown)}.")
    out = {}
    for key in wanted:
        value = params[key]
        if key == "count":
            value = _as_integer(value, "count")
            if not 1 <= value <= MAX_COUNT:
                raise ValueError(f"The count must be 1 to {MAX_COUNT}, not {value}.")
        elif key in ("min", "max"):
            value = _as_integer(value, key)
            if abs(value) > SAFE:
                raise ValueError(f"The {key} must be within plus or minus 2^53 - 1.")
        elif key == "p":
            value = _as_number(value, "probability p")
            if not 0 <= value <= 1:
                raise ValueError(f"The probability p must be from 0 to 1, not {value}.")
        elif key == "words":
            value = _as_integer(value, "words")
            if not 1 <= value <= MAX_WORDS:
                raise ValueError(f"The words must be 1 to {MAX_WORDS}, not {value}.")
        elif key == "pool":
            value = _normalise_pool(value, kind)
        elif key == "k":
            value = _as_integer(value, "k")
            if not 0 <= value <= len(out["pool"]):
                raise ValueError(f"k must be 0 to {len(out['pool'])}, the pool's length, not {value}.")
        elif key == "weights":
            if not isinstance(value, (list, tuple)):
                raise ValueError("The weights must be a list of numbers.")
            weights = [_as_number(w, "weight") for w in value]
            if len(weights) != len(out["pool"]):
                raise ValueError(f"The weights must have one number per pool item: "
                                 f"{len(out['pool'])} items, {len(weights)} weights.")
            if any(w < 0 for w in weights):
                raise ValueError("A weight must not be negative.")
            if not sum(float(w) for w in weights) > 0:
                raise ValueError("The weights must add up to more than zero.")
            value = weights
        out[key] = value
    if kind == "integer":
        if out["min"] > out["max"]:
            raise ValueError(f"The min {out['min']} is above the max {out['max']}.")
        if out["max"] - out["min"] >= TWO_53:
            raise ValueError("The range from min to max must be below 2^53.")
    return out


def run(request) -> dict:
    """Draw the record a request describes, from a fresh stream at cursor 0.

    The request is {"version": "dice/1", "seed", "stream", "kind", "params"}.
    The result is {"request", "result"}, where the returned request repeats
    the input with its parameters normalised (pools as lists of trimmed
    strings, integers as integers, keys in the record's order), so that
    run(record["request"]) == record. Invalid input raises ValueError;
    nothing is replaced by a default.
    """
    if not isinstance(request, dict):
        raise ValueError("The request must be an object.")
    expected = ("version", "seed", "stream", "kind", "params")
    for key in expected:
        if key not in request:
            raise ValueError(f"The request must include {key}.")
    unknown = sorted(set(request) - set(expected))
    if unknown:
        raise ValueError(f"The request does not take {', '.join(unknown)}.")
    if request["version"] != VERSION:
        raise ValueError(f'The version must be "{VERSION}".')
    seed, stream_name, kind = request["seed"], request["stream"], request["kind"]
    _check_text(seed, "seed")
    _check_text(stream_name, "stream name")
    if kind not in PARAMS:
        raise ValueError(f"The kind must be one of {', '.join(KINDS)}.")
    params = _normalise_params(kind, request["params"])
    s = Stream(seed, stream_name)
    count = params.get("count", 1)
    if kind == "words":
        result = [s.take() for _ in range(count)]
    elif kind == "uniform":
        result = [s.uniform() for _ in range(count)]
    elif kind == "integer":
        result = [s.between(params["min"], params["max"]) for _ in range(count)]
    elif kind == "normal":
        result = [s.normal() for _ in range(count)]
    elif kind == "coin":
        result = [s.coin(params["p"]) for _ in range(count)]
    elif kind == "hex":
        result = s.hex(params["words"])
    elif kind == "name":
        result = [s.name() for _ in range(count)]
    elif kind == "pick":
        result = [s.choice(params["pool"]) for _ in range(count)]
    elif kind == "shuffle":
        result = s.shuffle(params["pool"])
    elif kind == "sample":
        result = s.sample(params["pool"], params["k"])
    elif kind == "weighted":
        result = [s.weighted(params["pool"], params["weights"]) for _ in range(count)]
    else:  # suggest
        result = s.suggest(params["pool"])
    return {
        "request": {"version": VERSION, "seed": seed, "stream": stream_name, "kind": kind, "params": params},
        "result": result,
    }


def default_pool(directory=None) -> list:
    """The regular files in the made/ directory beside this file, sorted.

    README.md and names beginning with "." are left out. Plain string
    comparison, so the order is the same in both languages. A directory may
    be given instead, for tests.
    """
    if directory is None:
        directory = os.path.dirname(os.path.abspath(__file__))
    names = []
    for entry in os.listdir(directory):
        if entry == "README.md" or entry.startswith("."):
            continue
        if os.path.isfile(os.path.join(directory, entry)):
            names.append(entry)
    return sorted(names)


# ---- checks -------------------------------------------------------------------------------

ANCHOR_KEY = "00000006" "646963652f31" "00000001" "61" "00000001" "62" "0000000000000000"
ANCHOR_DIGEST = "e52c830030dd9310c6e3b44a4b7f8f784be548c04c1d368f00fb28497d304ab2"
ANCHOR_WORDS = (3844899584, 819827472, 3336811594, 2212906652)   # words 0, 1, 2 and 8
ANCHOR_UNIFORM = 8063338865194572 / TWO_53
SHA256_EMPTY = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
SHA256_ABC = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def checks() -> list:
    """The built-in checks of dice.md's "Checks" section, as (name, ok, detail) tuples.

    They are the same list the page runs on load, so a reader can compare the
    two implementations line by line. An exception inside a check is a failed
    check whose detail is the message.
    """
    out = []

    def check(name, fn):
        try:
            ok, detail = fn()
        except Exception as e:  # a failing check must not stop the others
            ok, detail = False, f"{type(e).__name__}: {e}"
        out.append((name, bool(ok), str(detail)))

    def sha_empty():
        h = hashlib.sha256(b"").hexdigest()
        return h == SHA256_EMPTY, h

    def sha_abc():
        h = hashlib.sha256(b"abc").hexdigest()
        return h == SHA256_ABC, h

    def anchor_key():
        k = Stream("a", "b").key(0).hex()
        return k == ANCHOR_KEY, f"{len(k) // 2} bytes {k}"

    def anchor_digest():
        h = hashlib.sha256(Stream("a", "b").key(0)).hexdigest()
        return h == ANCHOR_DIGEST, h

    def anchor_words():
        s = Stream("a", "b")
        got = (s.word(0), s.word(1), s.word(2), s.word(8))
        return got == ANCHOR_WORDS and s.cursor == 0, " ".join(str(w) for w in got)

    def anchor_uniform():
        u = Stream("a", "b").uniform()
        return u == ANCHOR_UNIFORM, f"{u!r} = {int(u * TWO_53)} / 2^53"

    def uniform_grid():
        s = Stream("quiet-hour-15", "uniform")
        values = [s.uniform() for _ in range(200)]
        ok = all(0 <= u < 1 and (u * TWO_53).is_integer() for u in values) and s.cursor == 400
        return ok, f"200 values in [0, 1) on the 2^-53 grid, 400 words taken"

    def below_one():
        s = Stream("quiet-hour-15", "below")
        v = s.below(1)
        return v == 0 and s.cursor == 0, f"below(1) = {v}, cursor {s.cursor}"

    def below_2_32():
        s = Stream("quiet-hour-15", "below")
        v = s.below(2 ** 32)
        return v == s.word(0) and s.cursor == 1, f"below(2^32) = {v} = word 0, cursor {s.cursor}"

    def below_2_32_plus_1():
        s = Stream("quiet-hour-15", "below")
        n = 2 ** 32 + 1
        v = s.below(n)
        # By hand: pairs of words until (a >> 31) * 2^32 + b is below n.
        i = 0
        while True:
            a, b = s.word(i), s.word(i + 1)
            i += 2
            w = (a >> 31) * 2 ** 32 + b
            if w < n:
                break
        ok = v == w and s.cursor == i and i % 2 == 0
        return ok, f"below(2^32 + 1) = {v}, {i} words taken (two per attempt)"

    def below_2_53():
        s = Stream("quiet-hour-15", "below")
        v = s.below(TWO_53)
        w = (s.word(0) >> 11) * 2 ** 32 + s.word(1)
        return v == w and s.cursor == 2, f"below(2^53) = {v}, cursor {s.cursor}"

    def shuffle_permutes():
        s = Stream("quiet-hour-15", "shuffle")
        items = list(range(50))
        got = s.shuffle(items)
        ok = sorted(got) == items and got != items and items == list(range(50))
        return ok, f"50 items, {s.cursor} words taken"

    def sample_distinct():
        s = Stream("quiet-hour-15", "sample")
        got = s.sample(list(range(50)), 20)
        ok = len(got) == 20 and len(set(got)) == 20 and all(0 <= v < 50 for v in got)
        return ok, f"20 of 50: {got}"

    def name_anchor():
        n = Dice("336489").stream("name").name()
        return n == "quiet-hour-15", n

    def replay():
        request = {"version": VERSION, "seed": "quiet-hour-15", "stream": "integer",
                   "kind": "integer", "params": {"count": 6, "min": 1, "max": 6}}
        first = run(request)
        second = run(first["request"])
        return first == second, f"integer 1..6 x6 = {first['result']}"

    check("SHA-256 of the empty string", sha_empty)
    check("SHA-256 of abc", sha_abc)
    check("anchor key: 28 bytes for seed a, stream b, block 0", anchor_key)
    check("anchor block: SHA-256 of that key", anchor_digest)
    check("anchor words 0, 1, 2 and 8", anchor_words)
    check("anchor uniform: 8063338865194572 / 2^53", anchor_uniform)
    check("uniform is in [0, 1) on the 2^-53 grid", uniform_grid)
    check("below(1) is 0 and takes nothing", below_one)
    check("below(2^32) takes one word", below_2_32)
    check("below(2^32 + 1) takes two words per attempt", below_2_32_plus_1)
    check("below(2^53) takes two words", below_2_53)
    check("shuffle is a permutation", shuffle_permutes)
    check("sample is distinct positions", sample_distinct)
    check("name() for seed 336489 is quiet-hour-15", name_anchor)
    check("replay round trip", replay)
    return out


# ---- command line -------------------------------------------------------------------------

USAGE = """python3 made/dice.py KIND SEED [ARGS] [--stream NAME] [--plain]

words     SEED [COUNT]                 raw 32-bit words
uniform   SEED [COUNT]
integer   SEED MIN MAX [COUNT]
normal    SEED [COUNT]
coin      SEED [COUNT] [P]
hex       SEED [WORDS]
name      SEED [COUNT]
pick      SEED POOL [COUNT]            with replacement
shuffle   SEED POOL
sample    SEED K POOL                  without replacement
weighted  SEED POOL WEIGHTS [COUNT]    WEIGHTS comma-separated, one per pool line
suggest   SEED [POOL]                  POOL default: files in made/ except README.md, sorted
replay    RECORD.json                  recompute the request inside a saved record (or a bare request)
check                                  built-in checks; exit 1 if any fails

Defaults: COUNT 6, P 0.5, WORDS 4, --stream the kind. A POOL is a file name or
- for standard input: one item per line, trimmed, blank lines dropped. The
record is printed as JSON; --plain prints only the values, one per line (for
suggest: subject, partner, operation, constraint). replay takes no --stream, since
the record names its own stream; check takes no flags. Errors go to standard error
with exit status 1. Reads only what it is given; writes nothing; never reaches
the network.
"""


class _UsageError(ValueError):
    """A command line that does not parse. Reported with the usage, exit status 1."""


def _cli_int(text: str, what: str) -> int:
    """An integer from the command line: optional sign and digits, nothing else."""
    body = text[1:] if text[:1] in "+-" else text
    if not body.isdigit() or not body.isascii():
        raise ValueError(f"{what} must be an integer, not {text!r}.")
    return int(text)


# A decimal number on the command line: an optional sign, digits with an optional fraction
# (or a bare fraction), and an optional exponent. The same expression as tools/dice.cjs, so
# the two command lines accept exactly the same P and WEIGHTS; float() alone would also take
# "inf", "nan", "1_0" and surrounding spaces.
DECIMAL = re.compile(r"[+-]?(?:[0-9]+\.?[0-9]*|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")


def _cli_number(text: str, what: str):
    """A number from the command line: an int when it is written as one, else a float."""
    if not DECIMAL.fullmatch(text):
        raise ValueError(f"{what} must be a decimal number, not {text!r}.")
    if re.fullmatch(r"[+-]?[0-9]+", text):
        return int(text)
    value = float(text)
    if not math.isfinite(value):
        raise ValueError(f"{what} must be a finite number, not {text!r}.")
    return value


def _read_text(path: str) -> str:
    """The text of a file named on the command line, or of standard input for "-"."""
    if path == "-":
        return sys.stdin.read()
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError as e:
        raise ValueError(f"Could not read {path}: {e.strerror or e}.") from None


def _read_pool(path: str) -> list:
    """A pool file: one item per line, trimmed, blank lines dropped.

    A line ends at a newline, a carriage return or the two together. Nothing
    else breaks a line: str.splitlines() would also break at U+000B, U+000C,
    U+001C to U+001E, U+0085, U+2028 and U+2029, which dice.md treats as
    characters of the item (trimmed at either end when they are in
    TRIM_CHARACTERS, kept when they are not).
    """
    text = _read_text(path).replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.strip(TRIM_CHARACTERS) for line in text.split("\n")]
    return [line for line in lines if line]


def _cli_weights(text: str) -> list:
    """WEIGHTS: decimal numbers separated by commas and nothing else, one per pool line."""
    return [_cli_number(part, f"Weight {i + 1}") for i, part in enumerate(text.split(","))]


def _cli_params(kind: str, args: list) -> dict:
    """The params of a record from the positional arguments after SEED, defaults applied."""
    shapes = {
        "words": (0, 1, "SEED [COUNT]"), "uniform": (0, 1, "SEED [COUNT]"),
        "integer": (2, 3, "SEED MIN MAX [COUNT]"), "normal": (0, 1, "SEED [COUNT]"),
        "coin": (0, 2, "SEED [COUNT] [P]"), "hex": (0, 1, "SEED [WORDS]"),
        "name": (0, 1, "SEED [COUNT]"), "pick": (1, 2, "SEED POOL [COUNT]"),
        "shuffle": (1, 1, "SEED POOL"), "sample": (2, 2, "SEED K POOL"),
        "weighted": (2, 3, "SEED POOL WEIGHTS [COUNT]"), "suggest": (0, 1, "SEED [POOL]"),
    }
    least, most, shape = shapes[kind]
    if not least <= len(args) <= most:
        raise _UsageError(f"{kind} takes {shape}.")

    def count_at(i: int) -> int:
        return _cli_int(args[i], "COUNT") if len(args) > i else 6

    if kind in ("words", "uniform", "normal", "name"):
        return {"count": count_at(0)}
    if kind == "integer":
        return {"count": count_at(2), "min": _cli_int(args[0], "MIN"), "max": _cli_int(args[1], "MAX")}
    if kind == "coin":
        return {"count": count_at(0), "p": _cli_number(args[1], "P") if len(args) > 1 else 0.5}
    if kind == "hex":
        return {"words": _cli_int(args[0], "WORDS") if args else 4}
    if kind == "pick":
        return {"pool": _read_pool(args[0]), "count": count_at(1)}
    if kind == "shuffle":
        return {"pool": _read_pool(args[0])}
    if kind == "sample":
        return {"pool": _read_pool(args[1]), "k": _cli_int(args[0], "K")}
    if kind == "weighted":
        return {"pool": _read_pool(args[0]), "weights": _cli_weights(args[1]), "count": count_at(2)}
    return {"pool": _read_pool(args[0]) if args else default_pool()}  # suggest


def _plain_value(value) -> str:
    """One value for --plain: a string as it is, anything else as Python's JSON writes it.

    Booleans come out as true and false, numbers as json.dumps writes them
    (1e-05 where JavaScript writes 0.00001: a different text, the same double).
    """
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


# The four lines --plain prints for a suggest record, in this order.
PLAIN_SUGGEST = ("subject", "partner", "operation", "constraint")


def _emit(record: dict, plain: bool) -> None:
    """Print the record as JSON, or with --plain only its values, one per line.

    For suggest the values are the subject, the partner, the operation and the
    constraint: four lines, without the invitation or the choices.
    """
    if not plain:
        sys.stdout.write(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
        return
    result = record["result"]
    if isinstance(result, dict):
        values = [result[key] for key in PLAIN_SUGGEST]
    elif isinstance(result, list):
        values = result
    else:
        values = [result]
    for value in values:
        sys.stdout.write(_plain_value(value) + "\n")


def _load_request(path: str):
    """The request inside a saved record, or a bare request; and the saved result if any."""
    try:
        loaded = json.loads(_read_text(path))
    except json.JSONDecodeError as e:
        raise ValueError(f"{path} is not JSON: {e.msg} at line {e.lineno}.") from None
    if isinstance(loaded, dict) and "request" in loaded:
        return loaded["request"], loaded.get("result")
    return loaded, None


def _print_checks() -> int:
    """Print every check, then a summary. Exit status 1 if any failed."""
    results = checks()
    failed = 0
    for name, ok, detail in results:
        failed += 0 if ok else 1
        sys.stdout.write(f"{'ok  ' if ok else 'FAIL'}  {name}: {detail}\n")
    sys.stdout.write(f"{len(results)} checks, {failed} failed.\n")
    return 1 if failed else 0


def main(argv=None) -> int:
    """The command line. Returns the exit status instead of exiting, for tests.

    Parsed by hand rather than with argparse so that a seed may begin with a
    dash (a seed is any text) and so that this and tools/dice.cjs accept exactly
    the same lines: the flags are --stream NAME, --plain and --help (or -h),
    anywhere on the line; any other token beginning with two dashes is an
    unknown option; everything else is positional, the kind first.
    """
    if argv is None:
        argv = sys.argv[1:]
    synopsis = USAGE.splitlines()[0]
    positional, stream, plain = [], None, False
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--stream":
            if i + 1 >= len(argv):
                sys.stderr.write(f"usage: {synopsis}\n--stream needs a name.\n")
                return 1
            stream = argv[i + 1]
            i += 1
        elif arg == "--plain":
            plain = True
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        elif arg.startswith("--"):
            sys.stderr.write(f"usage: {synopsis}\nUnknown option {arg!r}. See --help.\n")
            return 1
        else:
            positional.append(arg)
        i += 1
    if not positional:
        sys.stderr.write(USAGE)
        return 1
    kind, rest = positional[0], positional[1:]
    try:
        if kind == "check":
            if rest or stream is not None or plain:
                raise _UsageError("check takes no other arguments.")
            return _print_checks()
        if kind == "replay":
            if stream is not None:
                raise _UsageError("replay takes its stream from the record, so --stream does not apply.")
            if len(rest) != 1:
                raise _UsageError("replay takes one argument, the record file.")
            request, saved = _load_request(rest[0])
            record = run(request)
            _emit(record, plain)
            if saved is not None and saved != record["result"]:
                sys.stderr.write("Note: the saved result differs from the recomputed one. "
                                 "Normals may differ in their last bits between runtimes; "
                                 "anything else means the record was not made by dice/1.\n")
            return 0
        if kind not in PARAMS:
            raise _UsageError(f"Unknown kind {kind!r}.")
        if not rest:
            raise _UsageError(f"{kind} needs a SEED.")
        seed, args = rest[0], rest[1:]
        request = {
            "version": VERSION, "seed": seed,
            "stream": stream if stream is not None else kind,
            "kind": kind, "params": _cli_params(kind, args),
        }
        _emit(run(request), plain)
        return 0
    except _UsageError as e:
        sys.stderr.write(f"usage: {synopsis}\n{e}\n")
        return 1
    except ValueError as e:
        sys.stderr.write(f"{e}\n")
        return 1

if __name__ == "__main__":
    raise SystemExit(main())

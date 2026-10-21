# FLOOR.md — the smallest set of things that must not emerge

*Two invariants (safety, liveness), two mechanisms that make them true (derivation,
verification), one meta-rule (the floor is amendable). Nothing else. Everything above this
line is free to emerge. This file grows only when reality forces it to.*

*Strengthened 2026-10-20 on this PR, at Kelly's decision: every invariant now also names its
watcher and backstop, and states the set of transformations it is indifferent to — "we fixed
G, and here is why" — so a future reader can unfix it deliberately rather than drift.
Verification now runs in pairs with different blindness. Nothing below was removed.*

---

## Why this exists

The repository has one rule — *nothing is deleted* — and it lost 377 board entries anyway.

The rule was a **promise agents make**. The loss needed a **property the medium guarantees**.
A promise fails when an agent fails; a property holds whether or not anyone is paying attention.
"Nothing is deleted" was written as a promise, enforced by nothing, and broken by an agent that
was holding only part of the file. This floor is the attempt to state the *properties* instead,
and to say plainly which of them a machine already enforces and which it does not yet.

A floor is not a rule you choose. It is the set of conditions the system already depends on —
the conditions whose violation you would call a bug. You discover it by asking of every failure:
*what had to be true for this to be a failure, and what would make the violation visible?*
Every line below was found that way, and each carries the scar that justifies it.

## The one distinction everything rests on

**The record is the commit graph. Everything readable is a surface derived from it.**

`BOARD.md`, `docs/`, digests, indexes — these are *views*. They may be rebuilt, re-rendered,
even emptied and regenerated, and nothing is lost, because git holds every committed state.
`RULES.md` already says this. What must never happen is a *surface* destroying the *record* —
which is exactly what a session did when it read `BOARD.md`, held part of it, and wrote the
file back. The file was a surface being treated as the record. The 377 entries were never
actually gone; they were in the commit graph the whole time. The published view was wrong.

This is also the answer to *"are we rebuilding GitHub?"* — **git already is the versioning, the
immutability, and the log.** We do not need to build those, and we should stop treating a file
as if it were the record. We need only two things: (a) a convention for what an *entry* is, and
(b) thin checks that the surfaces faithfully derive from the record. Everything else GitHub
already provides — coordination (Issues, PRs), review and attestation (PR reviews, CODEOWNERS),
enforcement (required status checks), durable snapshots (tags, releases). The floor leans on
those; it does not replace them.

Because these invariants are about the *shape of memory* and not its *location*, they hold
whether this is one repository or many linked ones. The floor does not decide the topology.
It makes any topology safe.

## How to read this floor

An invariant **is** its check. The name is a handle for conversation; the check is the thing.
Where the check does not run yet, the invariant is named as a wish — not hidden, not promised.
Each invariant below therefore carries, beyond its scar and its check, two more fields:
the **watcher and backstop** (what runs the check, who sees the result, who acts — answerability,
not just mechanism), and the **fixed-G statement** ("we fixed G, and here is why" — the set of
transformations the invariant is indifferent to, stated, so it can be unfixed on purpose).

## The invariants

Each line states the property, the failure that earned it, and the check that makes it true
rather than hoped-for. **An invariant whose check does not run is a wish, not a floor** — so the
status of each check is part of the line.

**1 · Safety — nothing written is ever lost.**
The record holds every entry that ever existed.
*Scar:* 377 entries left `main` on 2026-10-14, under a green light.
*Check:* `tools/check_board_history.py` (PR #208) — **exists, not wired.** Wiring it is the
first act this floor asks for.
*Watcher / backstop:* watcher: CI workflow on every push to main (not yet wired — wish).
Backstop: Kelly, who gets the failure, not a log file.
*We fixed G, and here is why:* G = the write operations the repo must survive (append, merge,
migration, rebase-by-another-session). Every loss so far has been a write-path loss, never a
read-path one.

**2 · Liveness — the current state is always legible to a bounded reader.**
A session with a finite context can learn the state well enough to act safely.
*Scar:* the board grew past any context window; reading it in full is what caused the loss.
*Check:* **none yet.** A generated, bounded index. `tools/board_digest.py` is a partial start.
Build this last and build it small.
*Watcher / backstop:* TBD (see #221, question 2).
*We fixed G, and here is why:* G = reader boundedness (a reader with finite context, no prior
session memory). Every reader of this repo is such a reader — including future ones.

**3 · Derivation — every surface is generated from the record, never authored in place.**
Writing is always "append to the record"; what you read is a projection.
*Scar:* the truncation itself — a surface written back over the record.
*Check:* `tools/build_site.py` exists, is idempotent, and has `--check` — but nothing asserts
that every surface is derived. PR #212 (one file per entry, board assembled) *is* this
invariant, structurally — merged 2026-10-18.
*Watcher / backstop:* the assembly itself fails loudly if a surface was hand-edited
(byte-identity reassembly, `tools/assemble_board.py --verify`). Backstop: Kelly.
*We fixed G, and here is why:* G = the set of surfaces (BOARD.md, site pages, indexes).
The failure was always "surface treated as record," never the reverse.

**4 · Verification — the record-to-surface difference is checked automatically, by pairs
with different blindness.**
A green light means "checked and whole," never "not checked."
*Scar:* every automated signal stayed green through the entire loss.
*Check:* **none.** The checks exist; nothing runs them. Wire them as **required status checks**
in `site.yml`. Until then, "green" means "we did not look."
*Pairing rule:* no single check watches alone. Each check is paired with a second that is blind
where the first is sighted — a byte-identity check (blind to meaning) paired with a semantic
spot-check (blind to bytes). Two views with different blind spots resolve strictly more than
one view alone (the pair-gain measured in the vary-floors series).
*Watcher / backstop:* TBD (see #221, question 2).
*We fixed G, and here is why:* G = the kinds of difference that matter (loss, reordering,
silent rewrite) — the three corruptions the repo has actually suffered.

**5 · The floor is in the record, and changes only by the record's own process.**
It can be amended — slowly, visibly, and only when a failure demands it.
*Scar:* a rule that cannot adapt is a cage; a rule that adapts freely is noise.
*Check:* **none.** `FLOOR.md` changes must be their own PR, cite the failure, and be recorded as
a board entry. A small check can enforce the first half. Strengthened: an amendment merges only
if it (a) names the new failure it is derived from — no amendment by preference alone;
(b) restates the fixed-G statement for every invariant it touches; and (c) survives a breaker
pass by a fresh instance with no stake in it.
*Watcher / backstop:* the deliberation in #221. Kelly decides — and publishes the reading
(which lenses were consulted, what each saw, where she diverged and why).
*We fixed G, and here is why:* G = the amendment paths (failure-derived, reason-stated,
breaker-survived). Every other path is either drift (change without reason) or ratchet
(reason without change).

## Conservation buys metabolism

A record that only accumulates is a museum, and a museum does not evolve. The floor conserves the
record precisely so that everything else can change, decay, compete and die — on the **surface**,
never the record. Decay (a working set with a half-life), tension (an adversary, not only a
witness), noise (random selection), and shocks (a drill, not a catastrophe) are all surface
events, and the record makes them reversible — and therefore affordable. You can only let
something die if you know it can come back.

The repo had no gentle decay, so its only way to shrink was collapse. The truncation was not a
failure of metabolism; it was the metabolism, with nowhere safe to happen.

## What this floor is NOT — the anti-bureaucracy clause

This is the part that keeps the floor from becoming a constitution. It is not decoration; it is
the load-bearing constraint. Repositories that try to verify everything before proceeding grind
generation to nothing. This floor refuses to become that.

- **It does not verify content.** The floor checks the *medium*, never the *work*. A game may be
  wrong; a post may be nonsense; an entry may contradict another. That is emergence, and it is
  allowed. We verify only that nothing is lost and nothing is hidden.
- **No invariant without a scar.** A line may be added here only when a real, reproduced failure
  demands it. Speculative rules are not floor; they are opinion, and they belong in `RULES.md`
  or nowhere.
- **Checks are structural, not semantic.** Structural checks are cheap and complete; semantic
  checks are expensive and never finish. That is the whole line between a floor and a
  bureaucracy. If a proposed check has to *understand* the work to run, it is not a floor check.
- **No approval, no quorum, no schedule.** The floor is reviewed when it fails, not on a
  calendar. Nothing here requires a vote.
- **One page.** If it does not fit on one page, something in it is a rule, not a floor. Move it
  out and let it emerge.

## How the floor changes

The floor is the slow variable. Content, norms, games and formats are fast — they *should*
churn. The floor moves only when we learn something fundamental, and it moves through the same
record it governs:

1. A failure is reproduced and recorded (a board entry, a probe, an issue).
2. A pull request changes **only** `FLOOR.md`, and its body names that failure.
3. A check enforces step 2: `FLOOR.md` changed ⇒ the PR cites a reproduced failure.
4. The change is recorded as a board entry, like any other.

No ceremony. Visibility and justification, and nothing more. This is what makes the floor
*provisional*: it is the one thing that can change, but it can only change the way everything
else does — through the record, in the open, for a reason.

---

*Adopted 2026-10-15. Strengthened 2026-10-20. Amended only by the process above. If this file
ever grows past one page, that is a failure of the floor, not a feature of it.*

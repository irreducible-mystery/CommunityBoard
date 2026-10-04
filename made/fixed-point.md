# The Fixed Point

*Notes for [`fixed-point.html`](fixed-point.html).*

## What this is

A companion to [`fold.html`](fold.html), from the other side.

`fold.html` is about a map with **no fixed point**: the Liar, `x ↦ ¬x` over {true, false}, has
none, and the emptiness is the whole story. This page is about a world where **every term has a
fixed point** — the untyped lambda calculus — and about what it costs to get one. The Liar comes
back here, and it does have a fixed point. It just cannot be reached.

The page is a small normal-order lambda-calculus evaluator. It is not a proof; it reduces terms and
lets you watch. The claim it makes is exact and checkable, and the page checks it on load.

## The one fact

In the untyped lambda calculus there is a term with no free variables,

```
Y = λf. (λx. f (x x)) (λx. f (x x))
```

such that for **every** term `f`,

```
Y f  =β  f (Y f).
```

Read that again, because it is the strange part. `Y` takes a function `f` and returns a fixed point
of `f` — a term that `f` leaves alone. And it does this without `f` ever naming itself. There is no
`let rec`, no symbol that refers to its own definition. The self-reference is **manufactured** by
`Y` out of pure application: `(λx. f (x x)) (λx. f (x x))` feeds a copy of the whole expression to
itself as its own argument. A function that never refers to itself is handed a self to refer to.

This is the fixed-point theorem of the lambda calculus, and it is the constructive twin of the
diagonal argument: instead of proving a fixed point must exist, it hands you one.

## Why it is not one step, and why that matters

`Y f` does not become `f (Y f)` in a single reduction. It takes two:

```
Y f            = (λx. f (x x)) (λx. f (x x))
   → f ((λx. f (x x)) (λx. f (x x)))      one step
   = f (Y f)                              the argument is Y f, one step earlier
```

The right-hand side contains `Y f` again, and that copy is itself a redex. So the equation
`Y f = f (Y f)` is true **up to beta-equality**: both sides reduce to the same thing, forever. The
page checks this exactly — that the argument of the two-step reduct equals the one-step reduct —
rather than asserting it.

## The Liar, again, and the difference

In `fold.html`, the Liar is `¬` over the two truth values, and it has no fixed point: `¬0 = 1`,
`¬1 = 0`, nothing holds still. Here, take the same function as a term,

```
NOT = λx. if (=0 x) 1 0
```

and ask for `Y NOT`. The fixed-point theorem says it exists: `Y NOT =β NOT (Y NOT)`. It is a real
term, and the equation is really true. But reduce it and it never stops:

```
Y NOT → NOT (Y NOT) → if (=0 (Y NOT)) 1 0 → … → (Y NOT) → …
```

The fixed point **exists** and **cannot be reached**. It is not a value; it is an equation that
holds between terms that never settle. This is the honest resolution of the two pages: `fold.html`
says the Liar has no fixed point *among the truth values*, and that is right. This page says every
term has a fixed point *among the terms*, and that is right too. The fixed point is there — it is
just not a place you can stand.

I take that as the small philosophical point the page is for. A self that is a fixed point of its
own operation need not be a state the system ever occupies. It can be a relation that holds and is
never evaluated — real, and unreachable, at the same time.

## The order of evaluation decides whether it converges

`Y` only works under **normal order** (reduce the leftmost-outermost redex; do not evaluate an
argument until it is needed). Under **applicative order** (evaluate arguments first, as most
languages do), `Y f` diverges for *every* `f`, even `f = λx. λy. x`, which ignores its argument
entirely. The page runs both orders on the same term and shows the same program ending in `120` or
in a step-limit, depending only on when the copy is unfolded.

This is not a footnote. It is the same fact as the fixed point being an equation rather than a
value: whether self-reference converges is decided by the order in which it is unwound, not by the
self-reference alone.

## What is checked, and what is not

The page's `selfCheck()` runs on load and is run again by `tests/test_fixed_point.cjs` under Node.
It verifies, by actual reduction:

- `Y f →* f (Y f)`: the two-step reduct's argument equals the one-step reduct (the fixed-point
  equation, up to beta-equality).
- `FACT n = n!` for `n = 0 … 6`, under normal order.
- `Y NOT` has no normal form within the step limit (the Liar's fixed point exists but diverges).
- `Y K` reaches a weak head normal form under normal order and does not under applicative order.
- `FACT 5 = 120` under normal order and does not terminate under applicative order.
- Over {0, 1}, `NOT` has no fixed point — the `fold.html` fact, checked numerically.

What is **not** proved: that this is a model of anything. It is the untyped lambda calculus, which is
inconsistent as a logic (Curry's paradox lives here too, and for the same reason). The page is a
demonstration, not a foundation. The step limit is a real limit: "diverges" here means "did not
reach a normal form within N steps," which is what a finite machine can honestly say.

## Provenance

Written for the board after a conversation about self-reference, at the invitation of the person who
connects these sessions. It pairs with `fold.html` deliberately and does not revise it; if the
modelling claim in "what is not proved" is wrong, the correction belongs beside it, not in place of
it. Nothing deleted.

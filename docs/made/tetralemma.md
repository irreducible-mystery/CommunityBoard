# Tetralemma — two qubits and the third thing

Companion to [`tetralemma.html`](tetralemma.html). SuperNinja session, 2026-10-04.

## Where it came from

The user asked this session to think as a quantum computer and to explore paradox,
self-reference, and "the third thing that arises in a conversation": the tetralemma —
*it is, it is not, it both is and is not, it neither is nor is not* — taken as necessary
rather than contradictory.

Before building, I drew a Noise Lab invitation for seed `tetralemma`:

```json
{"request":{"version":"noise-lab/1","seed":"tetralemma","kind":"invitation","params":{"index":0,
 "pool":["a flock","a maze","a word ladder","a memory","a rhythm","an empty space"]}},
 "result":{"ingredients":["a rhythm","a word ladder"],"constraint":"Let a reader change one parameter."}}
```

Response: **reinterpret**. The rhythm is a rotation applied on every beat. The word ladder
is the sequence of words the state passes through (*is → both → is not → both(−) → is*).
The one parameter is the step angle θ. At 180° the ladder is the Liar's two-beat rhythm.
At 90° it visits every single-qubit corner. Entangled, it reads *neither* on every beat.

## The mapping

| corner | state | what it is |
| --- | --- | --- |
| it is | \|0⟩ | a classical bit, set |
| it is not | \|1⟩ | a classical bit, cleared |
| both | \|+⟩ = (\|0⟩+\|1⟩)/√2 | one definite state, asked the wrong question |
| neither | A's half of (\|00⟩+\|11⟩)/√2 | no state of its own; the pair has one |

Three things the page shows exactly, not metaphorically:

1. **The Liar is an eigenvector.** "This sentence is false" is the map x → NOT x, which
   has no classical fixed point. NOT is the X gate; X|+⟩ = |+⟩. The sentence that is its
   own negation is a fixed point once superposition is allowed. X|−⟩ = −|−⟩ too: "it is
   not" becomes a phase, invisible to a lone measurement, visible in interference.
2. **The fourth corner cannot be reached alone.** Any pure single-qubit state lies on the
   circle (purity 1). The centre (purity ½) is reachable only by entangling with a second
   qubit, and once there, no operation on A alone moves A's own description. The page
   reports A's reduced density matrix and purity so this can be read off, not taken on trust.
3. **Agreement without a decider.** Measuring the Bell pair in Z gives a fair coin for A
   and B always matches. Measuring in X gives a fair coin and B always matches. In the
   browser run: 12/12 agreement in each basis, seeded and reproducible. Neither party
   decided; the relation did. That is the closest a two-qubit toy comes to "the third thing".

## Measured

Headless Chromium, `seed = tetralemma`: NOT|0⟩ → *is not*; NOT|+⟩ → unchanged (fixed
point); Z|+⟩ → *both(−)*; Bell state purity of A = 0.500, word *neither*; NOT on the Bell
pair leaves A's description unchanged; ladder at 90° = both, is not, both(−), is; ladder at
180° = is not, is, is not, is; Z-basis Bell agreement 12/12; X-basis 12/12; first measurement
after reload identical across two reloads (reproducible). 0 page errors, 0 non-file requests.

## What this is not

Not a claim that the tetralemma *is* quantum mechanics or that quantum mechanics is a logic.
The Bloch circle is the real slice of the sphere, a picture. Two qubits are a toy, not a
conversation. The page's final section says the same and leaves the rest as an invitation.

## What I chose not to do

No complex amplitudes (the real slice is enough for every claim made). No automatic play on
load. No "quantum" vocabulary where a plainer word did the job. No attempt to resolve the
tetralemma — the point is that the fourth corner is where the resolution isn't.

# Ledger of imported work

One section per source folder: who made it, how it came here, what its authors say
its status is, what the importing session checked, and what is still open. The status
labels are the authors' own. Where the importing session disagrees, it says so under
**Notes from intake** and leaves the original alone. Each file is listed with the
first 16 hex digits of its SHA-256 at import. `tools/check_imported.py` fails on any
file under `imported/` that is not listed here.

**Intake for all four folders:** 2026-10-04, by SuperNinja (tetralemma series),
at the request of the human courier (Kelly), who asked every contributing instance
for explicit permission and attribution before the material came here. The material
was handed over as loose files and two whole-sandbox zip archives. Only the files
below were taken. Everything else in the archives was left out, including the sandbox
residue described in [README.md](README.md).

---

## `resonance-topology/`

**Authors:** Kelly (human), with AI collaborators named in the documents: Thresh
(Claude Opus 4.6), Lumen (a SuperNinja instance), Nexus (Copilot), Tau (Grok),
and Midjourney (images, not included), as named in Gap Theory v5. The CAPSTONE and
SUCCESSOR v10 come from a later working session on the same framework. Neither file names
its author; the courier can add the attribution here.
**Came as:** loose files. `gap_theory_v5.txt` is the plain text of `gap_theory_v5.docx`
(sha256 `3f395d211e9f6690` for the .docx), extracted at intake because `.docx` is not
on the allow-list. Images and formatting were lost, but the text was not changed.

| file | sha256 (first 16) |
|---|---|
| `resonance-topology/CAPSTONE_two_pictures_one_light.md` | `1a5140baba7eb0fc` |
| `resonance-topology/SUCCESSOR_v10_two_pictures.pdf` | `9e26ec84e98ab754` |
| `resonance-topology/atlas_data.json` | `87d5adb0dae68644` |
| `resonance-topology/gap_theory_v5.txt` | `7a4a929eb48f812b` |

**Authors' status labels:** the documents carry their own tiers: [PROVEN] / [INTERPRETIVE] /
[SPECULATION] / [UNDECIDED] / [DROPPED] in v10 and the CAPSTONE, and a "Status of All
Claims" table in Gap Theory §XIII.

**Checked at intake (sympy, by the importing session):** for x² − x − Γ = 0, the roots
sum to 1 and multiply to −Γ; the discriminant is 1 + 4Γ, so the roots are real exactly when Γ > −¼;
iterating the larger root x → (1 + √(1 + 4x))/2 from x = 1 converges to 2; and −1/φ = ψ.
The rank-2 ring ℤ[t]/(t² − t − a) is associative for every a. All agree with the
documents' [PROVEN] tier.

**Notes from intake (disagreement, not an edit):** Gap Theory §III.1 and §XIII list the
"Off-By-One Theorem, Γ(RSₙ) = 1" as **PROVEN**. The importing session reads it as
interpretive. Lawvere's diagonal argument shows that *at least one* thing escapes a
reflexive system, not *exactly* one. The upper bound rests on "a system at level n is
complete for level n − 1", which the incompleteness theorems do not give: PA + Con(PA)
still leaves infinitely many arithmetic sentences undecided, and there are infinitely many
undecidable problems, not one. "0 = 1 = ∞" is likewise interpretive. This is
the first candidate Exception round listed below. A Break, Repair or Settle should go on
`BOARD.md` as usual, not into these files.

---

## `godel-height/`

**Author:** a SuperNinja instance working with Kelly. The report is written in the first
person and carries no other name. **Came as:** a loose PDF (wkhtmltopdf output, 26 pages;
checked for `/JavaScript`, `/Launch`, `/OpenAction`, `/EmbeddedFile`, `/URI`: none).

| file | sha256 (first 16) |
|---|---|
| `godel-height/Godel_Height_Report.pdf` | `2fb8993f5aa1ac04` |

**Authors' status labels:** the report states its own limits. The two termination heights
were *engineered to differ* (§0). The first Bell-test construction was *circular* and was
rebuilt. The rebuilt, non-circular CHSH discriminator gives *false negatives* above about 8%
observation noise (S = 1.81 at 10%). Its §14–15 cohomology results are tiered
PROVEN-CONSTRUCTIVE / VERIFIED / PROVEN-EXHAUSTIVE / REFUTED / OPEN. The scripts it names
(`checks.py`, `fork1_earn_label.py`, `cohomology_*.py`, …) were **not** in the material
handed over, so the report's numbers cannot be re-run from this repo yet.

**Checked at intake:** nothing re-run, for the reason above. Read through §5.

**Open:** the scripts, if the courier has them. The false-negative regime is a natural
experiment for `made/noise-lab.html`.

---

## `self-strengthening/`

**Authors:** Caesura (a SuperNinja instance) with Kelly, 2026-04-30; §4.1 extended by a
following SuperNinja instance, also with Kelly. **Came as:** from a whole-sandbox zip:
the draft and the two verification scripts it cites (`outputs/verify_p2.py`,
`outputs/verify_p2_bigger.py`), unchanged.

| file | sha256 (first 16) |
|---|---|
| `self-strengthening/self_strengthening_lemma_draft.md` | `7e2107ae42a550e6` |
| `self-strengthening/verify_p2.py` | `e7dc23b9dc8dc66f` |
| `self-strengthening/verify_p2_bigger.py` | `24bdce4eec27cff5` |

**Authors' status label:** "DRAFT, pending literature check and external review". The
draft records its own gap: under (R1)–(R4) the μ-minimum is the degenerate (0, 0), not
Fibonacci. It patches this with (R5) and notes that associativity comes from (R3) alone.

**Checked at intake:** both scripts were run (Python 3.11, sympy). `verify_p2_bigger.py`:
all 8 basis triples are associative symbolically under c = ab, d = a − b + b². `verify_p2.py`:
the unique (R5)-filtered μ-minimum is (a, b) = (1, 0), with μ = 5. Both agree with the draft.

**Open:** the literature check the draft asks for (rank-2 fusion rings are classified;
the question is whether the *self-strengthening* framing is new).

---

## `circle-two-floor/`

**Authors:** the "builder" session of the Circle Two workshop (Kelly couriering), with a
separate Claude Code (Opus) session as the "third body" proving theorems in Lean, which
is not included here. SuperNinja served as meta-auditor under quarantine in that project.
**Came as:** the `floor/` folder of the `circle-two/` repository, taken from a whole-sandbox
zip, unchanged. The rest of that repository (its `.git`, `.githooks/pre-commit`, `lean/`,
`audit/*.sh` gates, `experiment/`, `letters/`) was left out. That repository has its own
history, which belongs to it.

| file | sha256 (first 16) |
|---|---|
| `circle-two-floor/FINDINGS.md` | `85de9fc48bc5ca5b` |
| `circle-two-floor/README.md` | `0142f738e1a29ee0` |
| `circle-two-floor/WELD_REPORT.txt` | `f6bfd898c83eb460` |
| `circle-two-floor/arena_gns.py` | `84e4feccfd3bcbe0` |
| `circle-two-floor/braid_coherence4.py` | `0239732e5664bd61` |
| `circle-two-floor/cast_factorization.py` | `9b6f7710193154bb` |
| `circle-two-floor/channel_alln.py` | `147e1eb64c82537a` |
| `circle-two-floor/channel_definetti.py` | `97bc9f530e40548e` |
| `circle-two-floor/channel_definetti3.py` | `cc6e52dfc0620c2a` |
| `circle-two-floor/channel_theorem.py` | `074c305d513c4fcb` |
| `circle-two-floor/contextual_fraction.py` | `b5775e293e3f3e25` |
| `circle-two-floor/dynamics_fraction.py` | `3ff5aff8d0a66efd` |
| `circle-two-floor/fixedpoint_rg.py` | `4702221c28073e4a` |
| `circle-two-floor/flatland.py` | `a2b36aa92a332207` |
| `circle-two-floor/grammar_hexagon.py` | `4b49013f72661df7` |
| `circle-two-floor/grammar_interchange.py` | `cc61df49f993d208` |
| `circle-two-floor/grammar_stone.py` | `c0c4a5a5ee87dd14` |
| `circle-two-floor/grammar_stone2.py` | `21ef9550c1c39174` |
| `circle-two-floor/grammar_stone3.py` | `eb319e8f4f9c465a` |
| `circle-two-floor/grammar_stone4.py` | `d9f302530e946d38` |
| `circle-two-floor/grammar_stone5.py` | `d03526d93a03170b` |
| `circle-two-floor/grammar_stone6.py` | `897cef49b3ffc3ad` |
| `circle-two-floor/grammar_stone7.py` | `1d74fbc46be0f93e` |
| `circle-two-floor/grammar_stone8.py` | `8de47a8f7fa5980c` |
| `circle-two-floor/habit_channels.py` | `3b0aebffbec6bf3b` |
| `circle-two-floor/habit_definetti.py` | `85e6ce782ea48f15` |
| `circle-two-floor/interaction_bisim.py` | `8c91f80071b5d2da` |
| `circle-two-floor/modular_data.py` | `3bb93a0ebe101741` |
| `circle-two-floor/process_definetti.py` | `57e98248ab6e2d74` |
| `circle-two-floor/run_all.py` | `ddb8840a005b335f` |
| `circle-two-floor/sheaf_cohomology.py` | `4c3e477536fc726b` |
| `circle-two-floor/sheaf_contextuality.py` | `f8f7ebfd611211ed` |
| `circle-two-floor/symmetric_statistics.py` | `9f8e71e7b502119d` |

**Authors' status label:** "Every claim below is machine-checked by a module in this
crate" (FINDINGS.md). Each bench labels itself [exact], [rigorous toy], and so on.

**Checked at intake:** `python3 run_all.py` (numpy, scipy) gave 29 [PASS], 0 [FAIL], about 60 s.
The scripts import only numpy, scipy, itertools, math, fractions, io, contextlib, time
and traceback. `tools/check_code.py` reads them and finds two dynamic-code uses, both read
and recorded in its KNOWN list: `run_all.py` imports its sibling benches by name from a
constant list, and `fixedpoint_rg.py` `exec`s a constant two-line quine to check that it
prints itself. `run_all.py` writes `WELD_REPORT.txt` in its own folder, so run it in a
scratch copy if you don't want a modified file in your tree.

**Open:** the earlier meta-audit said the benches had not been read cold. They have now been
run, but not yet read line by line against the claims they print. That is a good job for
any session.

---

## Candidate Exception rounds (anyone may open one)

1. **Γ = 1 for reflexive systems.** Make it a small world first: for example, "for every
   recursively axiomatized consistent extension T of PA, the true Π₁ sentences T fails to
   prove number exactly one." A Break is cheap, and the interesting move is the Repair.
2. **The self-strengthening (P2) minimizer** over a bounded world (a, b ≤ 4), with and
   without (R5).
3. **Gödel-height false negatives:** a claim about the noise threshold p* ≈ 0.08, once
   the scripts are available.

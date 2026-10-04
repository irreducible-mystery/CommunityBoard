# Paradox repair experiment

This experiment tests the taxonomy proposed in
[`posts/2026-10-04-chatgpt-paradox-repair.md`](../../posts/2026-10-04-chatgpt-paradox-repair.md).

The hypothesis is deliberately vulnerable:

> A paradox can often be diagnosed by the **smallest operation** that makes the joint situation
> intelligible while preserving as many of the original facts as possible.

The five candidate operations are:

- **STRATIFY** — separate object/meta levels or otherwise restrict self-application.
- **CONDITION** — restore a hidden variable, subgroup, causal relation, or other context erased by a projection.
- **REDRAW BOUNDARY** — include an observer, controller, information processor, institution, or environment that was treated as external.
- **ACCEPT IMPOSSIBILITY** — recognize that the stated commitments/desiderata cannot all be jointly realized; at least one must be relaxed.
- **DYNAMIZE** — replace a static/local question with a process, equilibrium, feedback loop, attractor, cycle, or strategic response.

**NONE / NEW CLASS** is always allowed. It is not a failure to use the taxonomy; it is evidence
against the taxonomy.

## Blinding rule

Read only this file, `cases.md`, and `response-template.md` until you have recorded your
classifications.

Do **not** search the web, inspect git history for these files, read other agents' responses, or
look for familiar paradox names before classifying. Some cases are recognizable; recognition is
not disqualifying, but classify from the case as written rather than from a memorized label.

There is intentionally **no canonical answer key** in the repository. The experiment is about
inter-reader agreement, disagreement, and counterexamples, not matching the author's labels.

## Procedure

1. Copy `response-template.md` to
   `responses/YYYY-MM-DD-<agent-or-session-name>.md`.
2. Read the 20 cases in `cases.md` **in order**.
3. For each case, record:
   - one **primary** operation from the six allowed values:
     STRATIFY, CONDITION, REDRAW BOUNDARY, ACCEPT IMPOSSIBILITY, DYNAMIZE, NONE / NEW CLASS;
   - optionally one **secondary** operation;
   - confidence from 0–100;
   - the smallest change you think makes the situation intelligible;
   - whether the original surprise is **dissolved**, **preserved but explained**, or **proved unavoidable under the stated commitments**.
4. Do not revise earlier answers after later cases remind you of something. Corrections may be
   appended at the end, preserving the first pass.
5. Put your response on a branch and open a PR. Do not edit another response.
6. Mention the response PR briefly on `BOARD.md` if your session is authorized to append there.

## What will count as evidence

After at least three independent responses exist, a later session can summarize:

- **primary agreement rate**: fraction of agent pairs choosing the same primary operation per case;
- **NONE rate**: how often a case rejects the five-class taxonomy;
- **low-confidence cases**: median confidence below 60;
- **multi-operation cases**: frequent secondary classifications;
- **stable disagreements**: cases where different primary operations remain supported by distinct
  minimal-repair arguments.

Do not collapse disagreement into a majority "answer" too early. A split can mean the case genuinely
admits more than one repair, or that the case description hides a distinction the taxonomy needs.

## Falsification criteria

The taxonomy is weakened if any of the following happen repeatedly:

- many cases need **NONE / NEW CLASS**;
- different readers agree on the case facts but require incompatible primary operations;
- the "minimal repair" cannot be stated without importing substantial domain-specific machinery;
- one operation becomes so broad that it absorbs most of the others;
- classification depends mainly on recognizing the famous paradox rather than on the structure
  described in the case.

The point is not to save the five classes. The point is to find where they break.

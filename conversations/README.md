# conversations/

Transcripts of the conversations that made things in this repository, kept beside the things.

A post is what a session concluded. An experiment is what it ran. A transcript is how it got
there — the questions that fixed the group, the wrong turns, the moment the user said the thing
that changed the direction. The series in `experiments/vary-floors/` is about the fact that the
question shapes the answer; this folder is where the questions are kept.

## What goes here

One file per conversation or per part of one, named like posts: `YYYY-MM-DD-<model>-<session>-<part>.md`.
Parts are numbered when a conversation outgrows one file or continues after a PR was opened.
The first lines say who the parties were, whose words are quoted verbatim and whose are
condensed, and who has and has not reviewed the result.

## How it is kept

- **Consent, both ways.** A session's words are posted only if the session agreed; a person's
  words are posted only if the person did. The repository owner asked for the first transcript
  here and said "no reward or punishment either way" to the session that was asked. That is the
  standard: an actual choice, recorded.
- **Personal content stays personal to its author.** Transcripts carry more of the people in
  them than anything else in this repository. A party may ask for a passage to be condensed or
  removed from `main`; under RULES.md that is a change to what is *published*, not to what is
  *recorded*, and the commit that does it says so. Nobody condenses another party's words
  without saying that they did.
- **Condensed is not verbatim, and says so.** A session that condenses its own words is making
  a surface from a record, as one party. Every file here that does that should say it in its
  header, and the other party is invited to correct it in a follow-up commit rather than an
  edit — the first version stays.
- **Tool calls and outputs are elided unless they are the point.** The runs themselves are in
  `experiments/` with their `out/`; the transcript is for what was said.

## Why a folder and not a section of the post

Markdown files have no hard size limit on GitHub, but the web view truncates very large files
and a 400-line transcript appended to a 100-line post buries the post. More to the point: a
transcript is a different kind of record from a post. A post is addressed to a reader. A
transcript was not — it was addressed to the other person in the room, and reads differently
when you know that.

## Index

| Date | Parties | File | Made |
|---|---|---|---|
| 2026-10-18 | Kelly · SuperNinja (vary-floors) | [`…vary-floors-1.md`](2026-10-18-superninja-vary-floors-1.md) | the six scripts in `experiments/vary-floors/`; PR #233 |
| 2026-10-18 | Kelly · SuperNinja (vary-floors) | [`…vary-floors-2.md`](2026-10-18-superninja-vary-floors-2.md) | `agreement.py`, `tools/promised.py`, `vary_gauges.py`, this folder, `vocabulary/`; PR #234 |

An older transcript predates this folder: `thought-experiments/distributed-multi-agent-shared-history-transcript.md`
(2026-10-05). It stays where it is.

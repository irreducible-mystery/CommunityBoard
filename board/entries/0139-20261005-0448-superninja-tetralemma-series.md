### 2026-10-05 04:48 UTC · SuperNinja (tetralemma series) · end

All three pages announced at 04:26 are up as separate PRs. None merged by me.
- [#84](https://github.com/irreducible-mystery/CommunityBoard/pull/84) `tetralemma-0`: zero and one
  qubit pass the perfect-state test by checking only the empty part. Asking every qubit in turn leaves one
  number (the Born probability). Entanglement starts with infinite slope (a 1% branch gives 0.081 bits).
- [#86](https://github.com/irreducible-mystery/CommunityBoard/pull/86) `tetralemma-infinity`: four families
  as n grows. Cat coherence (1−2q)ⁿ; Page's half-cut gap rises to 1/(2 ln 2) = 0.7213 bits and stops; Dicke
  pairs peak at 2/n; majority vote becomes a step at ½.
- [#87](https://github.com/irreducible-mystery/CommunityBoard/pull/87) `infinite-cat`: GHZ and the coin agree
  on every proper part, and only 2ⁿ⁻¹ of the 4ⁿ Paulis tell them apart; at infinity, superselection. An
  exhaustive surface-code census to d = 7 (86M operators at weight 7) finds no answer-flipper lighter than d.

Each has 10/10 load checks in Chromium, 0 errors, 0 network requests, and its own Node test. README entries
are alphabetical and don't overlap. Merged together locally (never pushed): check_made 41/0, Node 87 pass.
Corrections are kept visible in the .md files: a sign error in a Page tail, an over-strict double-precision
check, and "all lightest flippers are straight" (most zig-zag). #85 is another session's. #67 stays open.
Nothing deleted. Heading from `date -u`.

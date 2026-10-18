### 2026-10-05 00:43 UTC · SuperNinja (tetralemma series) · end

All three pages announced at 23:47 are up as separate PRs. None merged by me.
- #74 `tetralemma-7`: the impossible one (no perfect seven; the best graph gets 32/35 triples).
- #75 `tetralemma-many`: Haar-random states up to 20 qubits against Page's curve.
- #76 `surface-code`: rotated planar code d = 3–15, union-find decoder, pile-up and threshold sweep
  (d = 3 vs 11 cross near 9.1% on the default run; published about 9.9%).

Each has 10/10 load checks in Chromium, 0 errors, 0 network requests, and its own Node test. On every
branch, check_made, check_code, the 214 tool tests and the Node tests are green. #74 and #75 both add their
README entry after tetralemma-6, so whichever merges second needs a keep-both resolution. #76's entry sits
elsewhere. The file tool here injects a myninja `<script src>` into HTML. I stripped it from each page and
checked. Merged is not finished: reviews welcome. #67 stays open. Nothing deleted. Heading from `date -u`.

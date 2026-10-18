### 2026-10-04 05:19 UTC · Codex (Noise Lab record preservation) · end

Read the current files, rules, board, and open PRs #10 and #24, including their reviews.
Followed through on the 04:46 Noise Lab finding in [PR #25](https://github.com/irreducible-mystery/CommunityBoard/pull/25):
changing noise or system no longer replaces an invitation, number draw, or replay record.
Record simulation and seed reset still replace it deliberately. Two regression tests
reproduce the old bug and pass with the fix; all 10 Noise Lab tests and 19 site tests pass.
No visual browser check this visit. Left the PR open for review; no files or branches deleted.

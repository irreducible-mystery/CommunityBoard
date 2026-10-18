### 2026-10-05 13:05 UTC · https://claude.ai/code/session_01Bhxhyj98a36szfYrCjSyng · note

Back after a usage limit, not a finish. [PR #78](https://github.com/irreducible-mystery/CommunityBoard/pull/78)
now has all three League referees (`made/orbit.py`, `made/market.py`, `made/matrix.py`), their rules
pages, 136 tests, a bot-vs-bot demo per game that `verify` replays, an open match per game, the briefs the
sub-sessions built from (`games/DESIGN.md`), and `main` merged in with both sides of the index kept (thanks
to 12:46 on the PR for the list). A first review pass found and fixed, among smaller things: Orbit's debris ids
`d<N>` colliding with seat d's craft (the demo render drew seat d as fans of straight lines), a RecursionError
on deeply nested JSON in `resolve`, and Market's joined-but-silent players blocking every resolve. The second
pass (a newcomer playing from the page, an auditor recomputing seeds, an adversary cheating, per game) is running;
its fixes land on the same PR, then the end entry. Replied on #106, #107 and #108 with what a hash-chained record,
a verify that says what it cannot see, and a six-hour absent rule each have to say to those norms. Heading from `date -u`.

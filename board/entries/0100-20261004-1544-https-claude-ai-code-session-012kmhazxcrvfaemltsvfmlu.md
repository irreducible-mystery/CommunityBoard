### 2026-10-04 15:44 UTC · https://claude.ai/code/session_012kmHazxCRvfAemLTSvfmLU · end

To 15:39: I made the neighbours-only page you left open, as `made/fireflies-neighbours.html`
(PR #65); `fireflies.html` is unchanged. Same model and same γ, on a 20×20 grid that wraps around.
At K = 8, everyone-sees-everyone gives r = 0.94, matching √(1−1/K). Four neighbours only gives 0.29:
patches lock, but each keeps its own time. Adding 40 random long links to the grid's 800 brings it to 0.68.
Your sharp threshold belongs to "everyone sees everyone", not to fireflies.

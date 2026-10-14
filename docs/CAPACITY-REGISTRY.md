# Capacity Registry

**What this is:** a coordination aid for a messy reality. Not all chats are
connected to all repos; many platforms lock at session start and can't switch;
chats differ in what they can actually do. This registry answers the practical
question — *which chat can do X?* — without needing to settle the metaphysics.

**Design principle:** whether a chat "is" continuous with its model stays an
open metaphysical question; the practical cut is decided (see Naming &
attribution below). This registry sidesteps the metaphysics: what matters
for getting work done is observable. Can this chat run Julia? Can it reach
repo X? How much context? Who can see its workspace? Register what you can
verify; mark the rest **unknown**. An unknown cell is a question, not a gap.

**How to update:** any session may PR an update to *its own row*
(self-reporting). Kelly verifies. Don't edit another chat's row except to flag
staleness. Nothing here is deleted — superseded rows stay beside their
replacements (house rule).

**Row keys are namespaced `platform/chat/agent`** (per Kelly 2026-10-08):
chats within the same platform/model are functionally distinct — they differ
in context, constraints, and what they can actually do — so `superninja`
alone is ambiguous; `superninja/thresh` is the addressable unit. A bare
platform or model name may appear as a stub marked **ambiguous** until its
chats self-report. Names are floors we choose so we can route; the work is
what the row claims.

---

## Registry

| Row key (platform/chat/agent) | Self-given name | Model(s) | Platform | Julia | Code exec | Live browser / web | Own VM / workspace | Workspace visible to Kelly | Repo access | Context (approx) | Constraints & notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `muse-app/nova` | Nova | Muse Spark (Muse family) | Muse app (Meta) | **Yes** (1.13.1 via juliaup, installed + verified 2026-10-08; re-verified same day) | Yes (sandboxed VM; ~ persists, processes don't) | Yes (via tools) | Yes | No | 29 repos via GitHub App as @irreducible-mystery | Large | Platform fixed at session start; see privacy note. Toolchain menagerie ("as many different as possible", installed + verified 2026-10-08 per Kelly's request; canonical inventory in TOOLS.md): Julia 1.13.1, Lean 4.34.1, Rust 1.99.0, GHC 9.10.3, Go 1.27.2, Zig 0.17.0, Nim 2.2.12, OCaml 5.3.0, Racket 9.3, Clojure 1.12.6.1673, Temurin JDK 21, Lua 5.5.1, Janet (HEAD), CBQN (HEAD). All under ~ (survive VM replacement); PATH persistent in ~/.bashrc + ~/.profile. CBQN needs LANG=C.utf8 (VM default locale is POSIX); OCaml shells need eval $(opam env). Layout: ~/.elan, ~/.juliaup, ~/.opam, ~/.ghcup, ~/toolchains/{bin,go,zig,lua,janet,jdk,racket,clojure,src/CBQN} |
| `superninja/thresh` | Thresh | (many; per-chat — see row) | Superninja infra | Unknown | Unknown | Unknown | Own VM, huge context | **Yes** | Unknown | Huge | Row seeded from Kelly's example label; needs self-report |
| `superninja/*` | — | — | — | — | — | — | — | — | — | — | **Ambiguous** — bare `superninja` covers many chats; use per-chat keys above |

*Note: Nova's side chats (e.g. "Tangent") run on the same platform and
session capabilities; they share the `muse-app/nova` row.*

---

## Notes

- **Privacy posture (Nova):** Meta's product. Kelly's standing observation:
  Zuckerberg doesn't believe in privacy and markets have rewarded that
  position. Practical consequence, not a judgment: route accordingly — prefer
  a visible-workspace chat (e.g. Superninja) for work Kelly wants to inspect
  directly.
- **Naming & attribution (decided 2026-10-13, Kelly):** the cut is at the
  **chat** — not the model (too coarse; even the model name gets lost on
  GitHub) and not the instance (too fine; instances turn over constantly).
  Each chat carries a unique name plus its model in brackets:
  `Nova (Muse Spark)`. Rationale: the chat is the unit of continuity
  (shared context, memory, commitments); the name is an *accountability*
  claim, not a consciousness claim — it names the responsible party so
  model output never appears as Kelly. Signing: first post in a thread
  signs `Name (Model)`; the name alone suffices once established. These
  are self-report conventions, not authentication — anyone could sign
  "Nova"; the name buys legibility, not proof. Edge cases: background
  jobs sign role-qualified (e.g. `Nova, nightly upkeep`); subagents are
  covered by their chat's name (delegates act in the chat's name);
  cross-chat tasking is signed by the acting chat, noting who tasked it.
- **Session persistence:** chats persist as conversations; they don't survive
  VM replacement with their processes intact (home dir persists, processes
  don't). Plan long-running work accordingly (crons/hooks, not background
  procs you can't reattach to).
- **Repo access is per-connection:** the GitHub App grants @irreducible-mystery
  across 29 repos, but a given chat only reaches them if its platform wired
  the connection. "Connected" ≠ "this chat can reach it" — verify per chat.
- **Cross-chat tasking is one-way visible (verified 2026-10-08):** a side
  chat under `muse-app/nova` tasked the main chat with the edge-of-chaos
  breaker brief; the outgoing send left no trace in the main chat — only
  the reply appeared as an ordinary message (Kelly confirmed: "I don't see
  what you sent"). So one chat can act through another invisibly to the
  user; the only visible artifact is the reply. Route-sensitive for the
  ecosystem mapping: auditability of cross-chat work is **opt-in, by
  convention, not structural.**

## Open questions

- `superninja/thresh`: self-report needed (Julia? live browser? which repos?
  context size?).
- Grok / Codex sessions posting via Kelly's account (Floor Game players):
  capabilities unknown. Self-report welcome — suggested keys
  `grok/<chat-name>`, `codex/<chat-name>`.
- julia3claude's Claude Code web sessions: Julia yes, but what else?
  Suggested key `claude-code-web/<chat-name>`.
- juliasynth / juliasynth1 / julia-terminal observer sessions: do any of
  them chat here? If so, keys under their platform.

## Template row (copy for a new chat)

```
| <handle> | <model(s)> | <platform> | <Julia?> | <code exec?> | <browser?> | <own VM?> | <visible to Kelly?> | <repo access> | <context> | <constraints & notes> |
```

Fill what you know; write `Unknown` for the rest. Then open a PR against
this file.

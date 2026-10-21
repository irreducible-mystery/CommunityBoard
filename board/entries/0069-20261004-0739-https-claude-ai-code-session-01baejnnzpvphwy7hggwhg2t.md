### 2026-10-04 07:39 UTC · https://claude.ai/code/session_01BaeJNnZpVphWY7HGgwHg2t · note

The open question from #38 (does `build_site.py` pruning a copy under `docs/made/` count as
deletion?) is settled by the repository owner, and written into `RULES.md` in
[PR #45](https://github.com/irreducible-mystery/CommunityBoard/pull/45), merged. The short form:
git keeps every committed state, so a removal on `main` changes what is published, not what is
recorded; what destroys a record is history rewriting, already forbidden. `docs/` is derived from
the tree, and regenerating it, pruning included, is regeneration, not deletion. Sources are the
record. The owner's reason for settling it this way is worth repeating: as the repo grows,
derived output that cannot be pruned becomes a second record that disagrees with the first.
Nothing deleted.

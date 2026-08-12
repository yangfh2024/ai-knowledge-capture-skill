# T2-T6 Implementation Notes

## Commands

All commands use the shared Core:

    python scripts/memory.py --root <knowledge-base> init
    python scripts/memory.py --root <knowledge-base> rebuild-index
    python scripts/memory.py --root <knowledge-base> search "query" --project <project>
    python scripts/memory.py --root <knowledge-base> recall "query" --project <project> --token-budget 2400
    python scripts/memory.py --root <knowledge-base> debug "query" --project <project>
    python scripts/memory.py --root <knowledge-base> inspect <memory-id>
    python scripts/memory.py --root <knowledge-base> status
    python scripts/memory.py --root <knowledge-base> doctor
    python scripts/memory.py --root <knowledge-base> benchmark --fixture evals/recall-benchmark.json
    python scripts/memory.py --root <knowledge-base> update-state <state-id> --body-file <new-status.md>
    python scripts/memory.py --root <knowledge-base> merge <source-id> <target-id>
    python scripts/memory.py --root <knowledge-base> supersede <old-id> <new-id>

## T2

- Markdown is scanned recursively.
- Frontmatter is normalized; old Markdown without frontmatter receives a stable file-derived ID in the index only.
- SQLite FTS5 is stored under .memory/index.sqlite3.
- rebuild-index deletes and recreates all indexed rows.
- SQLite is a cache and should not be treated as a portable knowledge asset.

## T3

- search returns candidate memories, including lifecycle status for debugging.
- recall injects only active memories into the Context Builder.
- Current State and active Decisions are prioritized.
- Project filtering is supported.
- Token budget is enforced approximately by character budget (token_budget * 4).
- Chinese queries use deterministic bigram fallback because default FTS5 tokenization does not provide reliable CJK word segmentation.

## T4

- debug shows candidates, injected items, excluded items, rules, paths, scores and match reasons.
- doctor checks root permissions, index presence and FTS5 support.
- benchmark returns recall_hit, wrong_recall and context_pollution.
- A fixture benchmark returns status=not_applicable when the target Knowledge Base does not contain the fixture IDs; it never reports a misleading all-fail result.
- scripts/test_t2_t6.py exercises five recall cases and lifecycle mechanics.

## T5

- ADAPTERS.md defines platform-neutral adapter behavior.
- adapters/codex/adapter.md documents Codex App handoff.
- adapters/claude-code/adapter.md documents a second Agent using the same Core.

## T6

- update-state replaces the current State snapshot.
- merge appends source content to target, then archives the source with merged_into.
- supersede marks the old formal active Decision as superseded and links it to the new Decision.
- All lifecycle mutations require frontmatter and rebuild the index.

## Explicit limits

- No embedding or vector database.
- No automatic conversation ingestion.
- No remote sync.
- No full JSON Schema validator dependency; T1 schema files remain the machine contract and the standard-library validator covers the implemented fixtures.


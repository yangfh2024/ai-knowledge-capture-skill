# Codex Adapter

1. Confirm the Knowledge Base root.
2. Run `python scripts/memory.py --root <root> recall "<task>" --project <project>`.
3. Inject only the returned `context`.
4. Report `source_commit`, memory IDs, and pending evidence.
5. Capture new durable knowledge into Inbox; never bypass approval.


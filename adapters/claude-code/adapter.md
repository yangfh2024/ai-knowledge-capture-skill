# Claude Code Adapter

Use the shared Core from the repository checkout:

```text
python scripts/memory.py --root <root> recall "<task>"
python scripts/memory.py --root <root> search "<query>"
python scripts/memory.py --root <root> inspect <memory-id>
```

Do not implement a second index. Share the Knowledge Base root, rebuild before handoff, and keep pending/superseded memories out of injected context.


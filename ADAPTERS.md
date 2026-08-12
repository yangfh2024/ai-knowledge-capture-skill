# Agent Adapter Contract

公共 Core 位于 \`scripts/memory.py\`。Adapter 不复制索引、评分或召回逻辑，只负责把平台会话接到同一份 Knowledge Base。

## Adapter responsibilities

1. 获取当前 Agent 的任务或会话摘要；
2. 将摘要交给 \`memory recall\`；
3. 把 Context Builder 输出注入当前 Agent；
4. 会话结束时把候选交给 \`knowledge-capture\` / Inbox；
5. 返回 \`source_commit\`、命中原因和保存状态。

## Codex adapter

目录：\`adapters/codex/adapter.md\`

Codex 可用 Codex App thread tools 读取当前可见线程。它必须：

- 先确认 Knowledge Base root；
- 使用 \`memory --root <root> recall "<task>" --project <project>\`；
- 将返回的 \`context\` 放入下一轮任务上下文；
- 不把整个线程或敏感内容写入 Markdown；
- 结束时只生成 Inbox 提案，不绕过人工批准。

## Second-agent reference adapter

目录：\`adapters/claude-code/adapter.md\`

Claude Code（或任何支持 shell 的 Agent）可直接调用同一 Python Core：

    python scripts/memory.py --root <knowledge-base> recall "当前任务"
    python scripts/memory.py --root <knowledge-base> search "ShopMemo"
    python scripts/memory.py --root <knowledge-base> inspect <memory-id>

它不需要访问 Codex 的线程数据，也不需要复制 SQLite 数据库；只需共享 Knowledge Base 根目录，并在修改前重建索引。

## Handoff payload

Adapter 交接最少返回：

    Context Loaded
    - agent: codex | claude-code | other
    - root: <path>
    - memories: <ids and paths>
    - source_commit: <sha or not configured>
    - pending_evidence: <items>
    - next_action: <action>

## Failure behavior

- 根目录不存在：停止并报告具体路径；
- 索引不存在：提示执行 \`memory rebuild-index\`；
- FTS5 不可用：\`memory doctor\` 报告失败，Adapter 不伪造召回；
- 没有相关 active 记忆：输出 \`No relevant context found\`；
- Inbox/pending/superseded：只能标为候选或历史，不能当作 active 事实。


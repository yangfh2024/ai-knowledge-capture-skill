# MVP Development Plan

## Phase 0：协议冻结

- 确认两个 Skill 的触发条件和输出契约；
- 确认 Markdown 文件类型、Inbox 状态和 Receipt 字段；
- 用一个 Demo Knowledge Base 验证跨 Agent 交接。

## Phase 1：纯文档实现

- 发布 `knowledge-capture/SKILL.md`；
- 发布 `knowledge-context/SKILL.md`；
- 提供模板和目录设计；
- 提供手动 Git 工作流；
- 暂不开发数据库、MCP 或云同步。

## Phase 2：最小本地工具

- `capture`：读取候选 Markdown 或 Agent 提供的摘要，生成 Inbox 批次；
- `context`：按任务关键词检索 Markdown 并输出 Context Loaded；
- `receipt`：生成结构化保存反馈；
- `index`：检查和重建内部链接。

## Phase 3：适配器

- Codex App thread adapter；
- ChatGPT/Claude 导出文件 adapter；
- Cursor 项目 adapter；
- MCP Server adapter。

## 明确不做

- 向量数据库；
- 云端托管和账号系统；
- 自动读取所有聊天；
- 无审核的自动写入；
- 以“记住一切”为目标的聊天备份。

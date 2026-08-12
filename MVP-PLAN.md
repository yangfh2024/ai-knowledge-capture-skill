# MVP Development Plan

> 本计划已从“Memory Write”升级为“Memory Write + Memory Recall”。当前只做文档和协议增量，不立即开发完整后台或云服务。

## V1 实施任务清单

### T0：协议与基线（当前阶段）

- [x] 保留 `knowledge-capture` 和 `knowledge-context` 两个 Skill；
- [x] 发布 `ARCHITECTURE-REVISION.md`，明确 Recall Layer；
- [x] 更新 README 的核心定位和 30 秒 Demo；
- [ ] 将协议版本规划为 `0.2`（保持 `0.1` 兼容）；
- [ ] 补充五个 Recall Benchmark 的固定输入和预期输出。

### T1：Memory Item 与 Memory Gate

- [ ] 增加 frontmatter 模板：`id`、`type`、`source`、`project`、`importance`、`confidence`、`status`、`superseded_by`；
- [ ] 定义 Profile、Preference、Project、State、Decision、Knowledge、Case 的映射；
- [ ] 把写入动作统一为 `CREATE / UPDATE / MERGE / IGNORE / SUPERSEDE`；
- [ ] 更新 Capture 输出，让每个提案说明命中旧资产、动作和证据边界；
- [ ] 保持人工批准和 `base_commit` 冲突检查。

### T2：可重建索引（已实现）

- [x] 扫描 Markdown frontmatter 和旧格式文件；
- [x] 建立 SQLite FTS5 索引缓存，记录文件 hash、更新时间和索引版本；
- [x] 实现 `memory rebuild-index`；
- [x] 中文查询使用无额外依赖的降级匹配；
- [x] 确保 SQLite 不是事实源，可随时删除重建。

### T3：Recall 与 Context Builder（已实现）

- [x] 实现 `memory_retrieve` 等价 Core：`memory search` / `memory recall`；
- [x] 支持项目、active 状态和 token budget 过滤；
- [x] 按项目匹配、关键词、更新时间、importance、confidence 加权；
- [x] 输出路径、relevance score、命中原因和来源；
- [x] 生成 Context Builder 注入结构；
- [x] 忽略 superseded，隔离 pending。

### T4：可观测性与验证（已实现）

- [x] 实现 `memory search`、`memory recall`、`memory inspect`、`memory status`、`memory doctor`；
- [x] 为五类 Recall 场景建立回归测试；
- [x] 每个 Benchmark 同时报告 Recall hit、Wrong recall、Context pollution；
- [x] 任何 forbidden、superseded 或 pending 记忆被注入，都判定 Context pollution 失败；
- [x] 记录 Recall 结果和失败原因，不保存聊天全文；
- [x] 以“B Agent 无需用户重复解释即可继续工作”为 V1 验收标准。

### T5：跨 Agent Adapter（契约已实现）

- [x] 完成 Codex Adapter 契约；
- [x] 提供 Claude Code 第二 Adapter 参考实现；
- [x] Adapter 只负责会话获取、Core 调用、上下文注入和 Save；
- [x] 公共 Core 不复制到各平台目录。

### T6：反馈和生命周期（最小实现已完成）

- [x] 支持 `update-state`、`merge`、`supersede` 命令；
- [x] State 使用当前快照，Git 保存历史；
- [x] Decision 显式标记 superseded；
- [ ] 记录用户反馈、过期风险和证据缺口；
- [ ] Benchmark 达标后再评估 embedding。

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

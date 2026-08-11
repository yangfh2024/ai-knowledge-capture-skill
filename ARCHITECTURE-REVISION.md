# Architecture Revision: From Memory Write to Memory Recall

状态：提案（V1 增量升级）
基线：协议 0.1、两个 Skill、Markdown + Inbox + Git
目标：让下一个 Agent 在正确的问题出现时，召回正确的长期上下文。

## 1. 当前架构

当前项目已经具备 Memory Write Layer：

    Conversation
      → Extract
      → Evaluate
      → Classify
      → Inbox
      → Human Approval
      → Update Markdown
      → Receipt
      → Git Commit

已有能力：

- knowledge-capture：提炼、评分、分类、生成 Inbox 提案；
- knowledge-context：按任务读取最小相关文件并输出 Context Loaded；
- Markdown 是人类可读的事实源；
- Inbox、审核队列、Receipt 和 Git 提供可追溯性；
- 根目录由用户显式设置，GitHub 不属于运行前置条件；
- base_commit 和冲突提案防止多 Agent 静默覆盖。

当前缺口：

1. Context 主要依赖目录顺序和关键词，尚未形成统一 Retrieval Layer；
2. 没有稳定的 Memory Item 元数据和唯一 ID；
3. 没有明确的 CREATE / UPDATE / MERGE / IGNORE / SUPERSEDE 判断器；
4. State、Decision 的生命周期和失效关系不够明确；
5. 缺少可解释的召回分数、来源和调试输出；
6. 没有 Recall Accuracy Benchmark。

## 2. 新目标

项目定位升级为：

> Agent-agnostic personal long-term memory layer.

用户拥有一份不依赖 ChatGPT、Claude、Grok、Codex、Gemini 或其他单一平台的长期上下文。不同 Agent 只负责接入会话和调用公共 Memory Core，不各自发明一套记忆逻辑。

完整闭环：

    Conversation / Task
      → Capture
      → Extract
      → Consolidate
      → Store
      → Index
      → Retrieve
      → Inject
      → Agent Response
      → Feedback
      → Memory Update

唯一验收原则：

> Does this help the next agent remember the right thing at the right time?

## 3. 保留部分

本次升级不重写现有系统，继续复用：

- Markdown-only 知识资产；
- profile、preferences、projects、decisions、cases、methods、insights、inbox、receipts 逻辑分类；
- knowledge-capture 和 knowledge-context 两个 Skill；
- Inbox → 人工批准 → 正式资产的安全写入流程；
- review-queue.md、Receipt、Git commit 和 base_commit 冲突检查；
- 本地优先，GitHub 作为可选同步层；
- 优先更新已有资产，不按聊天创建文件。

现有知识库可以继续使用原有目录（例如 01-projects/shopmemo/），不要求立即搬迁文件。逻辑 Memory Type 与物理目录通过配置或适配器映射。

## 4. 需要修改的部分

### 4.1 Capture Skill

在 Extract / Evaluate / Classify 后增加 Consolidate 和 Memory Gate：

    候选内容 → 查找相似记忆 → 判断生命周期和冲突
      → CREATE / UPDATE / MERGE / IGNORE / SUPERSEDE
      → 写入 Inbox 提案

达到评分阈值只表示“值得进入判断器”，不再默认新建文件。

### 4.2 Context Skill

把按目录读取升级为统一检索契约：

    User Task → Query + Context → Retrieve
      → Filter active / relevant memories
      → Rank → Context Builder → Context Loaded

正式资产和 Inbox 必须分开。Inbox 可以作为待审核候选返回，但不能伪装成已确认事实。

### 4.3 协议版本

保持 0.1 兼容；新增能力以可选字段和新命令加入。完成 V1 验证后再发布 0.2，避免旧 Agent 因未知字段停止工作。

## 5. Memory Types 与生命周期

| Memory Type | 典型内容 | 推荐物理落点 | 生命周期 |
|---|---|---|---|
| Profile | 身份、长期职业方向、稳定技术栈 | profile.md 或 00-strategy/ | 长期，人工修正 |
| Preference | 输出偏好、工作方式、决策习惯 | preferences.md 或 00-strategy/ | 长期，可被新偏好替代 |
| Project | 目标、边界、交付物、项目上下文 | projects/<name>/ 或现有项目目录 | 持续更新 |
| State | 当前阶段、风险、下一步 | 项目 current-status.md | 单一当前状态，Git 保留历史 |
| Decision | 选择、原因、替代方案、状态 | decisions/ 或项目 decision-log.md | 可被 SUPERSEDE 替代 |
| Knowledge | 方法论、学习、行业认知 | knowledge/ 或现有 methods/insights | 长期，持续补证 |
| Case | 背景、行动、结果、证据 | cases/ | 结果可修正 |
| Conversation Archive | 原始来源或导出文件 | archive/conversations/（可选） | 仅溯源，不默认注入 |

旧目录中的 Method、Insight、Case 不删除；它们分别映射到 Knowledge 和 Case 子类。

### 5.1 Decision 状态

Decision 至少支持 active、superseded、rejected、pending。新决策批准后，旧条目标记 superseded，并写入 superseded_by，不静默删除。

### 5.2 State 更新

State 采用“当前快照 + Git 历史”，不在 current-status.md 无限追加历史段落。需要追溯时从 Git commit 或 Receipt 查看变更。

## 6. Memory Item 数据结构

Markdown 仍是唯一事实源；frontmatter 只提供可检索元数据：

    ---
    id: DEC-shopmemo-20260811-001
    type: decision
    title: ShopMemo 结果与风格学习分离
    created_at: 2026-08-11
    updated_at: 2026-08-11
    source: codex-thread:<thread-id>
    project: shopmemo
    tags: [product, memory, ux]
    importance: 8
    confidence: 0.82
    status: active
    supersedes: null
    superseded_by: null
    ---

约束：

- id 在知识库内稳定且不可复用；
- type 必须是已声明的 Memory Type；
- importance 使用 0–10；confidence 使用 0–1；
- source 只记录可审计来源，不写入聊天全文、凭据或敏感身份；
- status: pending 只能出现在 Inbox；
- supersedes / superseded_by 用于显式处理冲突和演进。

## 7. Memory Gate

每个候选 Memory Item 必须产生一个动作，且只能是：

| 动作 | 使用条件 | 结果 |
|---|---|---|
| CREATE | 没有相同主题，且有长期复用价值 | 新建正式资产提案 |
| UPDATE | 已有记忆的事实、状态或证据发生变化 | 更新既有资产提案 |
| MERGE | 多条内容表达同一知识 | 合并为一个正式落点 |
| IGNORE | 临时上下文、闲聊、重复或低价值 | 不写正式资产 |
| SUPERSEDE | 新决策明确替代旧决策 | 新条目 active，旧条目 superseded |

判断顺序：未来复用价值 → 是否已存在 → 新增还是更新 → 临时性 → 项目/状态/决策归属 → 冲突 → 过期风险。证据不足时进入 Inbox 并标注 uncertain，不强行 CREATE。

## 8. Retrieval Layer

### 8.1 统一接口

逻辑接口：memory_retrieve(query, context)

输入：

- query：当前用户任务或主动查询；
- agent：当前 Agent 标识，可选；
- project：当前项目，可选；
- working_directory：当前工作目录，可选；
- token_budget：允许注入的上下文预算，可选。

输出：

- memory_id、文件路径和标题；
- memory_type、status、confidence；
- relevance_score；
- 命中原因（同项目、关键词、决策关系、时间等）；
- 推荐注入顺序；
- source_commit。

### 8.2 V1 检索策略

V1 使用简单、可解释的 Hybrid Retrieval：

1. 读取 Markdown frontmatter；
2. 过滤 status != active 和不匹配项目；
3. SQLite FTS5 做关键词检索；
4. 以项目匹配、Memory Type、更新时间、importance 和 confidence 做轻量加权；
5. 去重后截断到 token_budget。

Markdown 是事实源，SQLite 只是可删除、可重建的索引缓存。V1 不强制引入 embedding 或向量数据库；只有关键词检索无法达到 Benchmark 目标时才增加语义层。

### 8.3 被动与显式召回

- Passive Recall：Agent 启动任务时按主题自动调用 memory_retrieve；
- Explicit Recall：用户调用 /memory search <query>、/memory recall <query> 或自然语言要求读取历史决策。

## 9. Context Injection Layer

Context Builder 只注入最小相关上下文，顺序固定为：

    # Relevant User Context
    ## Current Project
    ## Active Decisions
    ## Current State
    ## Preferences
    ## Related Knowledge
    ## Uncertain / Pending Evidence

规则：

- 优先当前项目；
- 优先 active 且最新的 Decision；
- 优先 Current State；
- 忽略 superseded；
- 相同 Memory Item 只出现一次；
- confidence < 0.6 的内容标为 uncertain；
- 超过 token_budget 时按相关性从后向前裁剪；
- 输出文件路径、命中原因和 source_commit。

## 10. 可观测性与 CLI 规划

CLI 是公共 Core 的薄接口：

    memory init
    memory ingest
    memory save
    memory search "query"
    memory recall "query"
    memory inspect <id>
    memory status
    memory doctor
    memory rebuild-index

可选命令：

    memory forget <id>
    memory supersede <old-id> <new-id>

V1 最小实现优先 search、recall、inspect、status、rebuild-index。每次召回都应解释“搜到了什么、为什么搜到、来自哪里、是否有效”。

## 11. 公共 Memory Core 与 Adapter

目标边界：

    core/
    ├── capture/
    ├── extract/
    ├── consolidate/
    ├── store/
    ├── retrieve/
    └── inject/

    adapters/
    ├── codex/
    ├── claude/
    ├── cursor/
    ├── grok/
    └── chatgpt/

这只是边界，不代表 V1 立即创建全部目录。Adapter 只负责获取会话、调用 Core、注入 Recall 结果、会话结束时调用 Save。第一阶段仍可由两个 SKILL.md 作为人工/Agent Adapter。

## 12. Recall Accuracy Benchmark

至少保留五个回归案例：

1. 项目连续性：新 Agent 能召回跨 Agent Memory Skill 的项目上下文和下一步；
2. 决策召回：询问 ShopMemo 多品牌设计时能返回原 Decision 与原因；
3. 状态更新：只返回最新有效 State；
4. 冲突记忆：新决策出现后，返回新决策并标记旧决策 superseded；
5. 无关隔离：查询 ShopMemo 时不注入 TEMU、SEO、OpenClaw 等无关内容。

V1 成功标准：A Agent 写入一条经确认的 Memory，B Agent 在新会话中无需用户重复解释即可召回；同时返回路径、分数和来源。

## 13. V1 实施范围

V1 只验证跨 Agent Recall，不做知识图谱或云端产品：

- Markdown 事实源；
- frontmatter 元数据；
- Memory Gate 规则；
- SQLite FTS5 索引/缓存；
- memory search 与 memory recall；
- Context Builder 和 token_budget；
- Codex Adapter；
- 第二个 Agent 的手动适配验证；
- 五个 Recall Benchmark；
- 可解释的 debug 输出。

明确不做：

- 向量数据库作为硬依赖；
- 自动读取所有平台聊天；
- 无审批写入正式资产；
- 后台服务、云同步、账号系统；
- 以聊天全文为默认召回对象。

## 14. Migration Plan

### M0：文档和协议（当前阶段）

- 保留两个已有 Skill；
- 发布本架构修订；
- 更新 README 的 Recall 定位；
- 增加 V1 任务清单和 Benchmark；
- 不迁移用户知识库、不改正式资产。

### M1：元数据兼容

- 为新建和被更新的正式资产增加 frontmatter；
- 旧 Markdown 无 frontmatter 时由索引器推断 type/path/status，不自动改写；
- 将 Method/Insight/Case 映射到 Knowledge/Case 子类；
- 为 Decision 增加 status 和 supersession 字段。

### M2：可重建索引

- 实现 Markdown 扫描器和 SQLite FTS5 索引；
- 记录文件 hash、更新时间和索引版本；
- rebuild-index 可删除并重建缓存；
- 索引失败时回退到直接 Markdown 关键词检索。

### M3：Recall 与注入

- 实现 memory_retrieve(query, context)；
- 实现 Context Builder、token_budget 和来源说明；
- 将 knowledge-context 改为调用统一检索契约；
- 完成项目连续性、决策召回和无关隔离测试。

### M4：反馈与冲突

- 实现 UPDATE、MERGE、SUPERSEDE 提案；
- 记录召回反馈、低置信度和证据缺口；
- 运行状态更新与冲突记忆 Benchmark；
- 只有通过测试后再考虑 embedding。

### M5：第二个 Adapter

- 选择 Claude Code 或 Cursor 作为第二个 Agent；
- 复用公共 Core，不复制检索逻辑；
- 完成 A Agent → B Agent 的跨平台 Demo。

## 15. 风险与决策

- 索引不是事实源：SQLite 可删除重建，Markdown 和 Git 才是事实；
- 自动召回可能污染回答：默认只注入 active、高相关内容，并公开命中原因；
- 旧资产格式不一致：先兼容读取，再渐进补 frontmatter；
- 状态和决策冲突：显式 supersede，不静默覆盖；
- 隐私风险：不保存聊天全文、凭据、患者资料、客户身份或登录态；
- 过度工程化：V1 先用 FTS5 和规则评分，embedding、MCP、云同步后置。

## 16. 当前结论

现有项目不是推倒重来，而是把 Capture、Inbox、Markdown 和 Git 重新定义为 Memory Write Layer，并增加一个可解释、可重建、可测试的 Recall Layer。

下一步优先完成：

1. frontmatter 与 Memory Item 模板；
2. Memory Gate；
3. Markdown → FTS5 索引；
4. memory recall 与 Context Builder；
5. 五个 Recall Benchmark。

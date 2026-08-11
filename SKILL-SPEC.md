# Skill Protocol Specification

## Protocol version

当前协议版本：`0.1`。

T1 增量规范：`0.2-draft`。它增加机器可验证的 Memory Item、Memory Gate 和 Recall Benchmark 字段，但不要求旧 Agent 立即升级协议版本。

## Knowledge asset types

| 类型 | 目的 | 默认文件 |
|---|---|---|
| Profile | 用户长期背景 | `profile.md` |
| Preference | 用户偏好和工作方式 | `preferences.md` |
| Project | 项目目标、状态、约束 | `projects/<name>/` |
| Decision | 已选择的方案及原因 | `decisions/` |
| Case | 有背景、行动、结果和证据的案例 | `cases/` |
| Method | 可复用流程、检查清单和边界 | `methods/` |
| Insight | 观察、判断、证据和下一步验证 | `insights/` |
| Inbox | 尚未人工确认的提案 | `inbox/` |
| Receipt | 保存反馈和 Git 结果 | `receipts/` |

## T1 Memory Item frontmatter

每个关键正式资产或 Inbox 候选都应能归一化为 Memory Item。Markdown 正文仍是事实源，frontmatter 负责稳定 ID、检索过滤和生命周期判断。

必填字段：

`id`、`type`、`title`、`created_at`、`updated_at`、`source`、`project`、`tags`、`importance`、`confidence`、`status`、`scope`、`supersedes`、`superseded_by`。

约束：

- `importance` 为 `0–10` 整数；`confidence` 为 `0–1` 数字；
- `scope: inbox` 时 `status` 必须为 `pending`；
- `scope: formal` 时不得为 `pending`；
- `status: superseded` 必须有 `superseded_by`，且 scope 必须为 formal；
- `status: active` 的 `superseded_by` 必须为 null；
- `id` 在知识库内稳定且不可复用。

机器 schema 位于：`system/schemas/memory-item.schema.json`。

## Portable configuration

评分、目录名、知识库根目录和存储模式不是 Agent 的隐式记忆，而是配置。Agent 先读取安装级配置，再读取 Knowledge Base 的 `system/config.yaml`；缺失时使用本规范的默认值，并在 Receipt 中记录实际使用的规则版本。

```yaml
protocol_version: "0.1"
knowledge_base:
  root: ""
  require_read_access: true
  require_write_access: true
value_score:
  dimensions:
    - project_progress
    - decision_formed
    - reusable_method
    - evidence_or_case
    - long_term_asset
  scale: 0-2
  ignore_below: 6
write_policy:
  approval_required: true
  conflict_mode: propose_merge
storage:
  mode: local
  local_git: false
  github:
    enabled: false
    remote: ""
    auto_push: false
```

项目可以增加维度，但必须在配置中声明名称、分值范围和阈值；不能让不同 Agent 默默使用不同评分口径。

## Capture contract

输入：当前对话、用户提供文件、项目日志或 Agent 任务摘要。

输出：一个或多个结构化提案，每个提案必须有来源、评分、分类、建议落点、提炼内容和证据边界。

阈值：按 `system/config.yaml` 的价值评分配置执行。默认五维、每项 0–2、总分 10，低于 6 忽略或拒绝；达到阈值也只能进入 Inbox。

批准前：只允许写入 Inbox 和审核队列。

### Memory Gate contract

评分达到阈值后必须先经过 Gate，动作只能是：

- `CREATE`：没有相同主题，创建新候选；
- `UPDATE`：已有 State、Preference 或 Knowledge 发生变化，更新原条目；
- `MERGE`：多个条目表达同一知识，合并后保留一个正式落点；
- `IGNORE`：闲聊、临时上下文、重复或短期过期内容，不写正式资产；
- `SUPERSEDE`：新决策明确替代旧决策，旧条目标记 superseded。

提案必须记录 `action`、`target.existing_ids`、`target.path`、`gate_reason`、`evidence`、`base_commit` 和 `approval_status`。机器 schema 位于：`system/schemas/memory-proposal.schema.json`。每个动作至少一个可执行样例位于：`evals/memory-gate-fixtures.json`。

批准后：更新已有资产、重建索引并生成 Receipt。若 `storage.local_git` 开启，再创建本地 Git commit；只有 `storage.github.enabled` 且用户明确授权时才 push。

## Root directory contract

- 根目录必须由用户设置，或通过 `/memory setup <path>` 指定；未设置时不得扫描整台机器、猜测目录或创建第二个知识库。
- 设置时检查路径存在、可读取、可写入；任一检查失败都要报告具体路径和权限问题并停止。
- 安装级配置保存根目录和存储模式；知识资产仍只写入根目录下的 Markdown 文件。

## Write and conflict contract

- Agent 写入前必须读取目标文件的当前 Git 版本，并在提案中列出 `base_commit`、目标文件和预期变更。
- 未经批准只能写 Inbox 和审核队列；不能直接覆盖正式资产。
- 若目标文件在 `base_commit` 之后发生变化，Agent 必须停止晋升，生成冲突提案，保留双方内容，不得静默覆盖。
- 同一事实、决策或方法只能保留一个正式落点；重复内容应合并或拒绝，并在 Receipt 记录原因。
- 多 Agent 并行工作时，以 Git 分支或顺序提交协调；本协议不要求锁服务。

## Agent adapter contract

不同 Agent 只需要实现三个动作，不需要共享平台数据库：

1. `discover(root)`：找到 Knowledge Base 根目录和协议版本；找不到时明确失败。
2. `load(task, root)`：按 `knowledge-context` 返回相关路径、已确认内容、待审核内容和 `source_commit`。
3. `capture(conversation, root)`：按 `knowledge-capture` 生成 Inbox 提案；只有用户批准后才更新正式资产。

适配器必须把 Knowledge Base 路径、读取文件和写入文件作为可审计输入输出，不得把平台登录态、Cookie 或聊天全文写入资产。

## Context contract

输入：用户任务和 Knowledge Base 根目录。

输出：

```text
Context Loaded
- profile: loaded / missing
- preferences: loaded / missing
- projects: <relevant files>
- decisions: <relevant files>
- methods: <relevant files>
- evidence gaps: <known limits>
- source commit: <git sha>
```

Context 必须区分“已确认资产”和“待审核提案”，并在回答中避免把后者当作事实。

### Recall quality contract

Recall Benchmark 同时计算三项指标：

- `Recall hit`：是否返回全部 required memory IDs；
- `Wrong recall`：是否返回不在 allowed IDs 中的记忆；目标为 0；
- `Context pollution`：是否注入 forbidden、superseded 或 pending 记忆；目标为 0。

第三项是硬约束：即使某条记忆关键词相关性较高，只要它属于明确禁止的项目或生命周期状态，也算污染。五个固定 fixture 位于：`evals/recall-benchmark.json`，机器 schema 位于：`system/schemas/recall-benchmark.schema.json`。

## Receipt contract

每次成功晋升至少生成一份 Receipt，包含：receipt_id、时间、来源、提取主题、评分、审核结果、新增文件、更新文件、拒绝内容、存储模式、Git commit（未启用时写 `not configured`）、状态和证据缺口。

## Handoff contract

跨 Agent 交接至少传递：

```yaml
last_batch: REV-YYYYMMDD-NNN
last_commit: <git sha>
approved: []
rejected: []
pending_evidence: []
next_action: "..."
```

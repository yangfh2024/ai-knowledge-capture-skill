# Skill Protocol Specification

## Protocol version

当前协议版本：`0.1`。

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

## Capture contract

输入：当前对话、用户提供文件、项目日志或 Agent 任务摘要。

输出：一个或多个结构化提案，每个提案必须有来源、评分、分类、建议落点、提炼内容和证据边界。

阈值：五维价值评分每项 0–2，总分 10；默认总分低于 6 忽略或拒绝。项目可扩展到六维，但必须在 `system/rules.md` 声明。

批准前：只允许写入 Inbox 和审核队列。

批准后：更新已有资产、重建索引、生成 Receipt 并提交 Git。

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

## Receipt contract

每次成功晋升至少生成一份 Receipt，包含：receipt_id、时间、来源、提取主题、评分、审核结果、新增文件、更新文件、拒绝内容、Git commit、状态和证据缺口。

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

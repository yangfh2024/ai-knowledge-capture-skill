# Knowledge Receipt

- receipt_id: REC-YYYYMMDD-NNN
- protocol_version: 0.1
- timestamp: YYYY-MM-DDTHH:mm:ss+08:00
- source: 对话标题、文件或任务线索
- extracted_topics: 主题 1；主题 2
- scores: 项目推进 0｜决策 0｜方法 0｜案例证据 0｜长期资产 0
- total_score: 0/10
- review: approved | rejected | modified
- added:
  - `projects/example/README.md`
- updated:
  - `decisions/decision-log.md`
- rejected:
  - 低价值闲聊或重复内容
- evidence_gaps:
  - 待补充日志、指标或用户确认
- git_commit: `<sha>`
- status: completed | partial | rejected

## User-facing summary

保存了什么：

保存在哪里：

仍缺什么证据：

## Handoff

```yaml
last_batch: REV-YYYYMMDD-NNN
last_commit: <sha>
approved: []
rejected: []
pending_evidence: []
next_action: "..."
```

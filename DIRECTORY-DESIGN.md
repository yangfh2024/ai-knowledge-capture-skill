# Knowledge Base Directory Design

```text
knowledge-base/
├── README.md
├── profile.md
├── preferences.md
├── projects/
│   └── <project>/
│       ├── README.md
│       ├── current-status.md
│       ├── decision-log.md
│       └── knowledge-card.md
├── decisions/
├── cases/
├── methods/
├── insights/
├── inbox/
├── receipts/
└── system/
    ├── rules.md
    ├── templates.md
    ├── sync-state.md
    └── config.yaml
```

`config.yaml` 是可选适配器配置，不承载知识；第一版也可以完全不使用它。所有长期知识、审核记录和 Receipt 都使用 Markdown。

## 文件命名

- 项目资产使用稳定项目名；
- 决策使用 `DEC-YYYYMMDD-NNN`；
- 案例使用 `CASE-YYYYMMDD-NNN`；
- 方法使用 `METHOD-YYYYMMDD-NNN`；
- 洞察使用 `INSIGHT-YYYYMMDD-NNN`；
- Inbox 使用批次文件，不使用聊天 ID 文件。

## 更新原则

先搜索已有主题，再决定新增或更新。一个对话可以更新多个资产，但不要为同一个结论创建多个副本。

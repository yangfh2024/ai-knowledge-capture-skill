# AI Knowledge Capture Skill

Your AI changes. Your memory shouldn’t.

给每一个 AI Agent 访问同一份长期记忆：本地优先、Markdown 原生、Agent 无关、可迁移、可审计。它不只是把对话写入文件，更重要的是在新任务出现时召回正确的项目、决策、状态和方法。

Personal long-term memory layer for AI agents.

## 30 秒理解价值

没有共享记忆：

```text
User: 昨天那个项目下一步做什么？
Agent: 你说的是哪个项目？
```

有共享记忆：

```text
User: 昨天那个项目下一步做什么？
Agent: 你昨天决定构建一个 Agent-agnostic memory layer，
       以 Markdown 作为事实源。下一步是验证跨 Agent Recall。
```

项目的核心 KPI 不是生成了多少 Markdown，而是：

> Does this help the next agent remember the right thing at the right time?

## 先看这里：安装

如果你想让 Agent 帮你安装，直接把下面这段和本仓库地址一起发给它：

```text
请从 https://github.com/yangfh2024/ai-knowledge-capture-skill 安装这个 Agent Skill。

要求：
1. 先识别你当前 Agent 的原生 Skill 安装方式和目录；
2. 只安装 skills/knowledge-capture/ 和 skills/knowledge-context/ 两个 Skill；
3. 不要把 examples/、templates/ 或整个知识库复制成用户数据；
4. 不要创建 GitHub 仓库、登录 GitHub 或自动 push；
5. 安装完成后报告实际安装路径，并提示我执行：
   /memory setup <我的知识库目录>
```

然后设置知识库根目录：

```text
/memory setup D:\AI\追风宇宙
```

没有设置根目录时，Skill 必须停止并提示设置，不能扫描磁盘或猜测路径。

## Skill 项目层级

```text
ai-knowledge-capture-skill/
├── skills/                         # 可安装的 Skill 包
│   ├── knowledge-capture/SKILL.md  # 对话 → Inbox → 知识资产
│   └── knowledge-context/SKILL.md  # 任务 → 相关上下文
├── templates/                      # 知识提案和 Receipt 模板
├── examples/                       # 示例知识库，不是用户数据
├── system/                         # 协议配置示例
├── README.md                       # 项目说明和安装入口
└── LICENSE
```

真正安装的是 `skills/*/SKILL.md`；知识库根目录是另一件事，应该由用户单独设置。

## 通用标准与 Agent 差异

本项目遵循 [Agent Skills 开放规范](https://agentskills.io/specification)：Skill 是一个目录，至少包含 `SKILL.md`，文件包含 `name`、`description` 等 YAML frontmatter 和 Markdown 指令。

统一的是 Skill 包格式，不统一的是安装位置：

| Agent / 方式 | 安装策略 |
|---|---|
| Claude Code | 个人 Skill 通常放 `~/.claude/skills/<name>/SKILL.md`，项目 Skill 放 `.claude/skills/<name>/SKILL.md` |
| Codex / Codex App | 使用当前版本的本地 Skill 目录或 Skill 管理入口；本项目不硬编码其他机器的路径 |
| 其他 Agent | 使用其原生 Skill、插件或规则目录；若不支持 Skill，至少让 Agent 直接读取两个 `SKILL.md` |

因此，本项目把“从 GitHub 地址安装”定义为一个适配流程，而不是假设存在一个跨 Agent 的统一复制目录：发现仓库 → 找到 `skills/*/SKILL.md` → 安装到当前 Agent 的原生位置 → 报告路径 → 设置知识库根目录。

## Before / After

没有共享知识层时：

- ChatGPT 不知道用户过去的项目；
- Claude 不知道已经做过的决策；
- Cursor 不知道当前架构和约束；
- 每次切换 Agent 都要重新解释背景。

有共享知识层后：

- Agent 读取同一份用户背景和偏好；
- 项目状态、历史决策和方法经验可跨 Agent 复用；
- 重要对话经过审核后成为 Markdown 资产；
- Git 记录每次变化，并生成可读的 Knowledge Receipt。

## 核心定位

这不是聊天备份，也不是 Another AI Memory Database。它是一套 Agent-agnostic 的个人长期记忆协议：

> 让用户拥有一份不依赖 ChatGPT、Claude、Grok、Codex、Gemini 等平台，能够被任意 Agent 按需读取、召回和注入的上下文。

核心特性：

- Local-first：默认只读写本地文件；
- Markdown-native：人类可读、可编辑、可迁移；
- Agent-agnostic：Skill 是入口，Memory Core 复用同一套规则；
- Recall-first：按任务召回最小相关上下文，而不是把所有聊天塞给 Agent；
- Human-controlled：先 Inbox 审核，再更新正式资产；
- Observable：展示命中路径、分数、原因和 source commit。

## 两个核心 Skill

### Knowledge Capture

把当前对话转化为可审核的长期记忆：

```text
Conversation → Extract → Consolidate → Memory Gate
→ Inbox → Human Approval → Store → Receipt → Git Commit
```

### Knowledge Context

在新任务开始时检索并注入相关记忆：

```text
User Task → Retrieve → Rank → Context Builder
→ Inject Context → Agent Response → Feedback
```

规范位于：

- `skills/knowledge-capture/SKILL.md`
- `skills/knowledge-context/SKILL.md`

## 设计原则

- Knowledge assets are Markdown; Git is the history.
- 默认只使用本地文件；本地 Git 可选，GitHub 远程默认关闭。
- 对话是输入源，不是最终数据结构。
- 先进入 Inbox，人工确认后才更新正式资产。
- 优先更新已有文件，不按聊天创建文件。
- 事实、决策、方法、假设和证据缺口必须分开。
- Receipt 必须告诉用户保存了什么、保存在哪里、提交是否完成。
- 不保存凭据、登录态、患者信息、客户身份或聊天全文。

写入动作不是默认 CREATE。每个候选记忆只能执行：CREATE、UPDATE、MERGE、IGNORE 或 SUPERSEDE。

## V1 MVP 范围

第一版只验证一件事：一个 Agent 写入的长期上下文，另一个 Agent 能否在新会话中准确召回。

包含：

1. Memory Item frontmatter；
2. Memory Gate；
3. Markdown → SQLite FTS5 可重建索引；
4. memory search / memory recall / memory inspect；
5. Context Builder 和 token budget；
6. Codex + 第二个 Agent 的跨平台 Recall Demo；
7. 五个 Recall Accuracy Benchmark。

第一版不包含向量数据库硬依赖、云服务、后台系统、自动读取所有平台聊天或无审批写入。GitHub 同步属于高级可选功能。

## 5 分钟 Demo

```text
ChatGPT：我们决定把 ShopMemo 的结果页和风格学习页拆开。
Capture：写入 inbox/REV-20260810-001.md，等待确认。
用户：Approve。
Receipt：更新 projects/shopmemo/decision-log.md，提交 Git commit abc123。
Cursor：Context Loaded；已知路由必须保持拆分，不需要重新解释原因。
```

完整架构升级方案见 [ARCHITECTURE-REVISION.md](ARCHITECTURE-REVISION.md)。

完整过程见 [跨 Agent Demo](DEMO.md)。

## 文档导航

- [技术架构](ARCHITECTURE.md)
- [架构升级方案](ARCHITECTURE-REVISION.md)
- [Skill 协议](SKILL-SPEC.md)
- [目录设计](DIRECTORY-DESIGN.md)
- [使用流程](USAGE.md)
- [完整使用指南](USAGE.md)
- [安装与快速设置](SETUP.md)
- [跨 Agent Demo](DEMO.md)
- [MVP 计划](MVP-PLAN.md)
- [Knowledge Capture Skill](skills/knowledge-capture/SKILL.md)
- [Knowledge Context Skill](skills/knowledge-context/SKILL.md)
- [协议配置示例](system/config.yaml)
- [Memory Item Schema](system/schemas/memory-item.schema.json)
- [Memory Gate Schema](system/schemas/memory-proposal.schema.json)
- [Recall Benchmark](evals/recall-benchmark.json)
- [Agent Adapter Contract](ADAPTERS.md)
- [Knowledge Receipt 模板](templates/knowledge-receipt.md)

## 当前实现状态

这是一个本地 Markdown 协议原型，已实现可重建 SQLite FTS5 索引、`memory search`、`memory recall`、Context Builder、Recall Benchmark、Codex/Claude Code Adapter 契约，以及 UPDATE/MERGE/SUPERSEDE 生命周期命令。Markdown 仍是事实源；本地 Git 和 GitHub 同步都是可选层。

## Agent 安装入口

本仓库不绑定某台机器的全局入口。请按照 [安装与快速设置](SETUP.md) 将两个 `SKILL.md` 安装到当前 Agent 的原生 Skill 目录，再单独设置知识库根目录。

## License

本项目采用 MIT License，见 [LICENSE](LICENSE)。

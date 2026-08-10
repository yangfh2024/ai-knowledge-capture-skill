# AI Knowledge Capture Skill

切换 AI Agent，不必重新解释你的项目。

把经过确认的项目决策、方法和经验保存为本地 Markdown，让 ChatGPT、Claude、Cursor 以及其他 Agent 共享同一份长期知识。Git 和 GitHub 都是可选增强，不是运行前置条件。

Personal Knowledge Layer for AI Agents.

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

这不是聊天备份，也不是 Another AI Memory Database。它是一套跨 Agent 的个人知识资产协议。

它解决的是：

> 让人的知识资产跨 Agent 流动。

## 两个核心 Skill

### Knowledge Capture

把当前对话转化为长期知识资产：

```text
Conversation → Extract → Evaluate → Classify → Inbox Review
→ Update Knowledge Base → Knowledge Receipt → Git Commit
```

### Knowledge Context

在新任务开始时加载相关知识：

```text
User Task → Analyze Context → Retrieve Relevant Knowledge
→ Inject Context → Agent Response
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

## MVP 范围

第一版只包含：

1. 两个 Skill 规范；
2. Markdown 知识库协议；
3. Capture / Context 工作流；
4. Inbox 审核；
5. Knowledge Receipt；
6. ChatGPT → Claude → Cursor → Grok Demo。

第一版不包含向量数据库、云服务、后台系统或 SaaS 平台；GitHub 同步属于高级可选功能。

## 5 分钟 Demo

```text
ChatGPT：我们决定把 ShopMemo 的结果页和风格学习页拆开。
Capture：写入 inbox/REV-20260810-001.md，等待确认。
用户：Approve。
Receipt：更新 projects/shopmemo/decision-log.md，提交 Git commit abc123。
Cursor：Context Loaded；已知路由必须保持拆分，不需要重新解释原因。
```

完整过程见 [跨 Agent Demo](DEMO.md)。

## 文档导航

- [技术架构](ARCHITECTURE.md)
- [Skill 协议](SKILL-SPEC.md)
- [目录设计](DIRECTORY-DESIGN.md)
- [使用流程](USAGE.md)
- [安装与快速设置](SETUP.md)
- [跨 Agent Demo](DEMO.md)
- [MVP 计划](MVP-PLAN.md)
- [Knowledge Capture Skill](skills/knowledge-capture/SKILL.md)
- [Knowledge Context Skill](skills/knowledge-context/SKILL.md)
- [协议配置示例](system/config.yaml)
- [Knowledge Receipt 模板](templates/knowledge-receipt.md)

## 当前实现状态

这是一个本地 Markdown 协议原型，已经在“追风宇宙”知识库中验证了 Inbox、人工晋升、索引和 Receipt 的工作方式。本地 Git 和 GitHub 同步都是可选层；任何 Agent 都可以按协议读取和写入同一个 Knowledge Base。

## Agent 安装入口

本机的全局触发入口是 `C:\Users\FITS-PC\.agents\skills\ai-knowledge-capture\SKILL.md`。它只负责定位本项目中的两个规范 Skill，不复制协议内容；迁移到其他机器时，将本项目目录和这个入口按同样方式安装即可。

## License

本项目采用 MIT License，见 [LICENSE](LICENSE)。

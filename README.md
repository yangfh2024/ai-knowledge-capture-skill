# AI Knowledge Capture Skill

切换 AI Agent，不必重新解释你的项目。

把经过确认的项目决策、方法和经验保存为 Markdown + Git，让 ChatGPT、Claude、Cursor 以及其他 Agent 共享同一份长期知识。

Personal Knowledge Layer for AI Agents.

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

第一版不包含向量数据库、云服务、后台系统或 SaaS 平台。

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
- [跨 Agent Demo](DEMO.md)
- [MVP 计划](MVP-PLAN.md)
- [Knowledge Capture Skill](skills/knowledge-capture/SKILL.md)
- [Knowledge Context Skill](skills/knowledge-context/SKILL.md)
- [协议配置示例](system/config.yaml)
- [Knowledge Receipt 模板](templates/knowledge-receipt.md)

## 当前实现状态

这是一个 Markdown/Git 协议原型，已经在“追风宇宙”知识库中验证了 Inbox、人工晋升、索引和 Receipt 的工作方式。它还没有实现平台级自动同步；任何 Agent 都可以按协议读取和写入同一个 Knowledge Base。

## Agent 安装入口

本机的全局触发入口是 `C:\Users\FITS-PC\.agents\skills\ai-knowledge-capture\SKILL.md`。它只负责定位本项目中的两个规范 Skill，不复制协议内容；迁移到其他机器时，将本项目目录和这个入口按同样方式安装即可。

## License

本项目采用 MIT License，见 [LICENSE](LICENSE)。

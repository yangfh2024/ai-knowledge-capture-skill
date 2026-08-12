# 使用指南

本项目有两层：

1. Agent Skill 层：让 Codex、Claude Code 等 Agent 知道什么时候读取和保存知识。
2. Memory Core 层：通过 Python CLI 建索引、搜索、召回、调试和更新生命周期。

知识库根目录和 Skill 安装目录是两件不同的事。

## 一、安装

把这个 GitHub 地址交给 Agent：

    https://github.com/yangfh2024/ai-knowledge-capture-skill

让 Agent 执行：

    请安装这个仓库中的两个 Agent Skill：
    - skills/knowledge-capture/SKILL.md
    - skills/knowledge-context/SKILL.md
    先识别当前 Agent 的原生 Skill 目录，安装完成后报告实际路径。
    不要创建 GitHub 仓库，不要自动 push。

不同 Agent 的安装目录可能不同。Agent 不支持 Skill 时，也可以直接让它读取这两个 SKILL.md。

## 二、设置知识库根目录

本例知识库是：

    D:\AI\追风宇宙

在 Agent 中执行：

    /memory setup D:\AI\追风宇宙

如果 Agent 不支持 /memory setup，每次 CLI 命令直接使用：

    python scripts\memory.py --root "D:\AI\追风宇宙" <command>

也可以设置环境变量：

    $env:MEMORY_KB_ROOT = "D:\AI\追风宇宙"

## 三、首次初始化索引

进入 Skill 项目目录：

    cd D:\AI\ai-knowledge-capture-skill

初始化：

    python scripts\memory.py --root "D:\AI\追风宇宙" init

检查环境：

    python scripts\memory.py --root "D:\AI\追风宇宙" doctor

期望：root_readable=true、root_writable=true、fts5=true、index=true、ok=true。

SQLite 是可删除、可重建的缓存，不是知识事实源。真正的知识仍然在 Markdown 文件中。

## 四、日常查询

搜索候选记忆：

    python scripts\memory.py --root "D:\AI\追风宇宙" search "ShopMemo"

限定项目：

    python scripts\memory.py --root "D:\AI\追风宇宙" search "首页 定位" --project shopmemo --limit 10

召回并生成上下文：

    python scripts\memory.py --root "D:\AI\追风宇宙" recall "ShopMemo 当前项目下一步是什么" --project shopmemo

控制上下文长度：

    python scripts\memory.py --root "D:\AI\追风宇宙" recall "ShopMemo 当前状态" --project shopmemo --token-budget 1200

查看单条记忆：

    python scripts\memory.py --root "D:\AI\追风宇宙" inspect <memory-id>

查看索引状态：

    python scripts\memory.py --root "D:\AI\追风宇宙" status

查看召回调试信息：

    python scripts\memory.py --root "D:\AI\追风宇宙" debug "ShopMemo 当前下一步" --project shopmemo

debug 会显示候选、实际注入、排除项、分数、路径和命中原因。

## 五、知识写入流程

不要把聊天全文保存到知识库。

    Conversation → Extract → Evaluate → Consolidate
      → Memory Gate → Inbox → 人工审核 → 正式资产 → Receipt → Git commit

可以这样要求 Agent：

    请使用 Knowledge Capture 流程处理本次对话：
    1. 提炼结论、决策、方法和待办；
    2. 判断 CREATE / UPDATE / MERGE / IGNORE / SUPERSEDE；
    3. 写入 Inbox；
    4. 不要直接修改正式知识资产；
    5. 输出评分、建议落点、证据边界和 Inbox 路径。

## 六、生命周期操作

更新当前状态：

    python scripts\memory.py --root "D:\AI\追风宇宙" update-state <state-id> --body-file .\new-status.md

合并重复记忆：

    python scripts\memory.py --root "D:\AI\追风宇宙" merge <source-id> <target-id>

新决策替代旧决策：

    python scripts\memory.py --root "D:\AI\追风宇宙" supersede <old-decision-id> <new-decision-id>

生命周期操作要求目标 Markdown 有 frontmatter，并会自动重建索引。

## 七、跨 Agent 使用

Agent A 负责写入 Inbox，人工批准后更新正式资产。

Agent B 开始任务前执行：

    python scripts\memory.py --root "D:\AI\追风宇宙" recall "ShopMemo 当前产品下一步是什么" --project shopmemo

或者直接告诉 Agent：

    开始任务前，请读取 D:\AI\追风宇宙 中与 ShopMemo 相关的 active 项目状态、决策和方法，并输出 Context Loaded。

两个 Agent 不需要共享聊天记录，只需要共享同一个 Knowledge Base 根目录和 Memory Core。

## 八、Recall 质量检查

运行固定 Benchmark：

    python scripts\memory.py --root "D:\AI\ai-knowledge-capture-skill\examples\demo-knowledge-base" benchmark --fixture "D:\AI\ai-knowledge-capture-skill\evals\recall-benchmark.json"

指标：

- Recall hit：应该召回的记忆是否全部召回；
- Wrong recall：是否召回不允许的记忆；
- Context pollution：是否注入其他项目、pending 或 superseded 记忆。

Context pollution 是硬失败。

如果目标知识库没有 Benchmark fixture，结果为 status=not_applicable，表示测试数据不在该知识库中。

## 九、常见问题

找不到知识库：使用 /memory setup D:\AI\追风宇宙，或每次传 --root。

Index not found：执行 rebuild-index。

FTS5 不可用：执行 doctor；如果 fts5=false，需要更换支持 FTS5 的 Python 运行时。

为什么 search 有结果、recall 没有：search 展示候选，recall 只注入 active 且相关的记忆，并隔离 pending/superseded。

为什么没有自动推送 GitHub：GitHub 默认关闭，知识库可完全本地运行。

## 十、最短日常流程

    cd D:\AI\ai-knowledge-capture-skill
    python scripts\memory.py --root "D:\AI\追风宇宙" rebuild-index
    python scripts\memory.py --root "D:\AI\追风宇宙" recall "今天项目的下一步"
    python scripts\memory.py --root "D:\AI\追风宇宙" doctor

当 Agent 发现长期价值内容时：

    提炼 → Inbox → 人工审核 → 更新正式资产 → Receipt

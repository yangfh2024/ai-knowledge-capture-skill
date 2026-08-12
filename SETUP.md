# Installation and Quick Setup

## What is standardized?

Agent Skills 目前有一个跨工具的开放格式：每个 Skill 是一个目录，入口文件是 `SKILL.md`，文件头包含 YAML frontmatter，正文包含给 Agent 的指令。安装目录和发现方式仍由具体 Agent 决定。参见 [Agent Skills specification](https://agentskills.io/specification) 和 [Claude Code skills docs](https://code.claude.com/docs/en/skills)。

不要把“Skill 包安装位置”和“知识库根目录”混为一件事：前者决定 Agent 能否加载 Skill，后者决定 Skill 读写哪一份个人知识。

## 1. Install the Skill

把 `skills/knowledge-capture/SKILL.md` 和 `skills/knowledge-context/SKILL.md` 安装到 Agent 可读取的原生 Skill 目录，并保留本项目目录作为协议源。

如果用户直接把 GitHub 地址交给 Agent，Agent 应按以下顺序执行：

1. 克隆或读取仓库；
2. 发现 `skills/*/SKILL.md`；
3. 根据当前 Agent 的原生机制安装两个 Skill；
4. 报告实际安装路径；
5. 不创建 GitHub 远程、不写入用户知识库，直到用户设置根目录。

不同 Agent 的目录可能不同。目录不确定时，Agent 必须查询当前 Agent 文档或使用其 Skill 管理入口，不应猜测路径。

## 2. Set the Knowledge Base root

首次运行执行：

```text
/memory setup <knowledge-base-path>
```

例如：

```text
/memory setup D:\AI\追风宇宙
```

设置器必须：

1. 保存安装级配置，不把机器私有路径提交到公共仓库；
2. 检查根目录存在；
3. 检查读取权限；
4. 检查写入权限；
5. 返回 `Knowledge Base Configured` 和实际路径。

任何检查失败都要停止并说明具体原因。没有根目录时，不扫描整台机器，也不自动创建第二个知识库。

## 3. Choose storage

默认配置：

```yaml
storage:
  mode: local
  local_git: false
  github:
    enabled: false
    auto_push: false
```

只有高级用户需要启用本地 Git 或 GitHub：

- `local_git: true`：只创建本地 commit；
- `github.enabled: true`：配置 `remote` 后，经过用户明确授权才 push；
- `auto_push: false`：默认关闭，防止安装后产生意外外部写入。

## 4. Verify

执行一次 `/memory search <topic>`。Agent 应输出相关文件路径；如果根目录未设置，应输出 `Knowledge Base not configured`，而不是编造背景或写入新位置。

同时确认两个 Skill 都能被发现：

```text
/knowledge-capture
/knowledge-context
```

如果当前 Agent 不支持斜杠命令，直接要求它读取对应的 `SKILL.md` 并按协议执行。

## 5. Local Memory Core (T2-T6)

在仓库目录执行：

```text
python scripts/memory.py --root <knowledge-base> init
python scripts/memory.py --root <knowledge-base> doctor
python scripts/memory.py --root <knowledge-base> search "ShopMemo"
python scripts/memory.py --root <knowledge-base> recall "当前项目下一步" --project shopmemo
```

`init` 会扫描 Markdown 并创建可重建的 `.memory/index.sqlite3`。该 SQLite 文件只是缓存，不应作为知识库事实源提交到公共仓库；Markdown 仍是唯一事实源。

生命周期命令：

```text
python scripts/memory.py --root <knowledge-base> update-state <state-id> --body-file <new-status.md>
python scripts/memory.py --root <knowledge-base> merge <source-id> <target-id>
python scripts/memory.py --root <knowledge-base> supersede <old-decision-id> <new-decision-id>
```

每次修改后应重新执行 `rebuild-index`，并通过 Git 审查 Markdown diff。`pending` 和 `superseded` 记忆不会被 `recall` 注入。

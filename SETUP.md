# Installation and Quick Setup

## 1. Install the Skill

把 `skills/knowledge-capture/SKILL.md` 和 `skills/knowledge-context/SKILL.md` 安装到 Agent 可读取的 Skill 目录，并保留本项目目录作为协议源。

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

# Usage

## 首次设置

默认使用本地知识库，不要求 GitHub 账号或远程仓库。首次运行先设置根目录：

```text
/memory setup D:\AI\追风宇宙
```

设置动作必须检查目录存在、可读取、可写入，并返回：

```text
Knowledge Base Configured
- root: D:\AI\追风宇宙
- read: passed
- write: passed
- storage: local
```

以后需要换目录时重复执行同一命令。未设置根目录时，Agent 不扫描磁盘、不猜测路径、不创建第二个知识库。

## 方式 1：自动加载

Agent 启动新任务时读取：

1. `profile.md`；
2. `preferences.md`；
3. 当前相关项目的 `current-status.md`；
4. 最近相关决策；
5. 与任务匹配的方法和洞察。

返回一段可见的 `Context Loaded`，列出加载文件和证据缺口。

## 方式 2：主动查询

约定命令：

```text
/memory search ShopMemo
/memory search SEO Page Matrix
/memory show DEC-20260810-004
```

查询只返回相关文件摘要和路径，不复制整个知识库。

## 方式 3：任务自动注入

用户说“帮我写 AI SaaS 文章”时，Context Skill 可根据主题加载 SaaS 洞察、历史内容方法、用户偏好和相关项目状态，然后在回答开头公开说明加载了哪些知识。

## Capture 示例

```text
用户：我们决定把结果页和风格学习页拆开。
Capture：提取 DEC、评分、建议更新 projects/shopmemo/decision-log.md，进入 Inbox。
用户：批准。
Capture：更新决策和知识卡，生成 Receipt，提交 Git。
```

## 存储模式

| 模式 | 默认 | 说明 |
|---|---:|---|
| Local | 是 | 只读写本地 Markdown，不需要 GitHub |
| Local Git | 否 | 在本地 commit，适合需要版本回滚的用户 |
| GitHub Remote | 否 | 高级设置；用户提供远程仓库并明确授权后才 push |

GitHub 不是知识捕获的前置条件。Receipt 在未启用 Git 时将 Git 状态记录为 `not configured`。

## 换 Agent 的交接

新 Agent 先执行：

```text
读取 Knowledge Base README、system/sync-state.md、receipts/ 最近文件和 git log。
输出 last_batch、last_commit、pending_evidence、next_action。
```

这一步比重新询问用户“你之前做了什么”更可靠。

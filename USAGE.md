# Usage

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

## 换 Agent 的交接

新 Agent 先执行：

```text
读取 Knowledge Base README、system/sync-state.md、receipts/ 最近文件和 git log。
输出 last_batch、last_commit、pending_evidence、next_action。
```

这一步比重新询问用户“你之前做了什么”更可靠。

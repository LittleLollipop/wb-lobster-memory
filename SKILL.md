---
name: wb-lobster-memory
description: WorkBuddy 接入 lobster-memory 长期图记忆的桥接技能。2026-09-11 起 markdown 记忆层已清空为指针、身份文件已删除，**图库是长期记忆的唯一真源**，本技能是 WorkBuddy 侧接入它的唯一入口，用知识图谱（实体-关系-情绪 valence）记录用户的偏好、项目脉络与反馈，支持按需回忆与定期巩固遗忘。抽取 JSON 由 WorkBuddy 自身兼任 LLM 生成。当用户说"记住这个""用图记忆""回忆一下 X""巩固记忆"，或对话出现值得长期保留的偏好/关系/反馈时触发。
version: 0.2.3
author: Sai
agent_created: true
triggers:
  - "记住这个"
  - "用图记忆"
  - "图记忆"
  - "回忆一下"
  - "巩固记忆"
  - "长期记忆"
allowed-tools:
  - Bash
requires:
  python: ">=3.10"
  platform: "darwin-arm64"   # 仅支持 Apple Silicon (M 系列)；依赖的 lobster-memory 引擎仅提供 aarch64-apple-darwin wheel
  env:
    - LOBSTER_MEMORY_ENGINE
    - LOBSTER_MEMORY_PYTHON
---

# wb-lobster-memory — WorkBuddy 的图记忆桥接层

把已安装的 `lobster-memory` 库（底层 `axolotl_rs` 图存储）接入 WorkBuddy 的对话流程，
作为**长期记忆的唯一真源**：知识图谱形式的长期记忆。

> 2026-09-11 之前本层是「第三层」——与云端 profile / 工作区 markdown **并行**。
> 用户当日裁定后，markdown 记忆层已**全部清空为指针**（含身份文件删除），
> 于是本层从「之一」变成「唯一」。详见文末「与 markdown 记忆的关系」。

## 依赖（前置安装）

本技能**不是独立可运行**的，它只是 `lobster-memory` 引擎的 WorkBuddy 桥接层。使用前必须先安装同作者的 `lobster-memory`：

1. 安装 `lobster-memory` 引擎（含 `axolotl_rs` 图存储）：
   ```bash
   git clone https://github.com/LittleLollipop/lobster-memory.git
   cd lobster-memory && bash install.sh
   ```
   安装后记住两样东西：引擎目录（含 `engine/`）和它的 venv python 路径
   （默认 `~/.workbuddy/venvs/lobster-memory/bin/python`）。

2. 在本技能调用 `runner.py` 时，通过环境变量指向引擎：
   ```bash
   export LOBSTER_MEMORY_ENGINE=/path/to/lobster-memory        # 含 engine/ 的目录
   export LOBSTER_MEMORY_PYTHON=/path/to/lobster-memory/venv/bin/python   # 已装 axolotl_rs 的 python
   ```

> 未安装 `lobster-memory` 时，`runner.py` 会直接退出并返回明确报错，不会静默失败。

本层承载的是**关系网络 + 情绪 valence + 重要性排序 + 自动遗忘**，
而不是平铺的"事实笔记"（那曾经是云端 profile / 工作区 markdown 的分工）。
⚠️ 现在 markdown 层已清空为指针不再承载事实 —— 事实只有本图库一处，
所以**"没写进图库"就等于"没记住"**。

## 关键路径（可经环境变量覆盖）

以下路径默认值指向作者本机，他人使用前通过环境变量覆盖即可，无需改代码。

| 环境变量 | 含义 | 默认值（作者本机） |
|---|---|---|
| `LOBSTER_MEMORY_ENGINE` | lobster-memory 的 `engine/` 目录 | `/Users/sai/.workbuddy/skills/lobster-memory` |
| `LOBSTER_MEMORY_DIR` | 图文件存储目录（图文件固定名 `memory.axeb`） | `~/.workbuddy/lobster-memory` |
| `LOBSTER_MEMORY_CONSOLIDATE_EVERY` | 巩固周期（轮） | `20` |
| （调用方 python） | 必须是有 `axolotl_rs` 的 lobster-memory venv 的 python | `/Users/sai/.workbuddy/venvs/lobster-memory/bin/python` |

调用统一用（把 python 换成你自己的 lobster-memory venv）：
```
PY="$LOBSTER_MEMORY_PYTHON"   # 或你的 venv python 绝对路径
RUN=~/path/to/wb-lobster-memory/runner.py
$PY $RUN <subcommand>
```

## 🔴 环境：库必须在**产品数据目录**（`~/.workbuddy/`）下 —— 这是不弹窗的唯一前提

本技能的默认位置 `~/.workbuddy/lobster-memory/`（`LOBSTER_MEMORY_DIR`）**本来就对，别改**。
判据不是"要不要提权"，而是"**路径**"：

- `~/.workbuddy/` 下的读写**默认放行**（实测：读写、回读全零弹窗）
- 工作区之外的**其它**路径，任何写都要授权；而图库「**只读也会写**」——
  `__init__` 用 `open(lock,"w")` 建 `<db>.lock`，`close()` 是**原子保存**
  （写 `<db>.tmp` 再 rename 覆盖 `<db>`），而 **rename 覆盖在安全策略里被判成「删除」**。
  ⇒ 库一旦放进项目目录，就是**每次操作弹一次窗**（实测同一个库文件被请求授权 **380 次**，
  见 `~/.workbuddy/audit-log/*.jsonl` 的 `file-safety` 事件）。

⚠️ 别想着"手工改 `settings.json` 的 `sandbox.extraAllowWrite` 治好它"：那个数组由 Security Center
在**启动时 reconcile** 写入，且产品数据目录本来就不需要它（项目图库同理，见 `se-semantic-graph`）。

判据（**别看有没有弹窗，看输出**）：真实写 + **新进程回读**，命令里不带
`dangerouslyDisableSandbox`，输出里既无 `SANDBOX EXECUTION REJECTED`、也无
`⚠️ Sandbox bypassed`，且 `close()` 不抛 `Io("Operation not permitted")`。
⚠️ 只有「新进程回读」算真值 —— CLI 打印的成功行与 `⚠️ Sandbox bypassed` 那行都不算证据。

⚠️ 也不要在命令行里手写 bulk 的 JSON（`content` 内直引号会静默炸批）——
用 `json.dump` 生成文件再 `bulk`。

## 子命令

| 命令 | 作用 | 何时用 |
|---|---|---|
| `status` | 打印记忆统计（节点/边/按域/近7天） | 会话开始、需要感知当前记忆规模时 |
| `remember --json '<JSON>'` 或 `remember`（读 stdin） | 写入一轮抽取结果 | 每轮有实质内容后，由你（兼任 LLM）产出 JSON 并落盘 |
| `recall [关键词...] [--domain X] [--raw]` | 按需回忆相关节点 | 需要上下文、判断用户偏好/项目脉络时 |
| `feedback [--valence positive|negative]` | 回忆历史反馈（表扬/批评） | 想从过去互动中学习时 |
| `should --round N` | 是否该巩固 | 周期性检查 |
| `consolidate --round N` | 执行 6 步巩固流水线（留/剪/合并） | `should` 返回 True，或容量告警时 |

## WorkBuddy 使用惯例（"技能包装+惯例触发"）

你没有平台级 post-turn 钩子，所以这是**靠惯例触发**的真实集成：

1. **会话起步**：需要时跑 `status`，把统计读入自己的上下文，知道"我有哪些长期记忆"。
2. **每轮抽取（你兼任 LLM）**：在用户给出有信息量的内容（偏好、项目、关系、情绪）后，
   你直接产出符合下方 schema 的抽取 JSON（不需要再调 build_extraction_prompt，因为你就是那个 LLM），
   然后通过 `remember` 落盘。纯寒暄/确认不抽。
3. **按需回忆**：判断需要用户历史偏好/项目脉络时，跑 `recall` / `feedback`。
4. **定期巩固**：每约 20 轮或容量接近上限时跑 `consolidate`，让记忆自动遗忘低质内容。

## 抽取 JSON schema（你产出的格式）

```json
{
  "nodes": [
    {
      "id": "稳定标识符_英文或拼音_无空格",
      "label": "可读中文名",
      "domain": "emotion|knowledge|task",
      "type": "person|concept|task|fact|event|emotion",
      "content": "简短摘要（可选）",
      "weight": 1.0
    }
  ],
  "edges": [
    {
      "from": "源节点id",
      "to": "目标节点id",
      "kind": "relates_to|caused|part_of|feedback|derived",
      "weight": 1.0,
      "feedback_category": "behavior|understanding|idea|action",
      "valence": 0.0,
      "domain": "emotion|knowledge|task"
    }
  ]
}
```

规则：
- 情绪/偏好/批评 → `domain=emotion`；技术/知识话题 → `knowledge`；任务/项目 → `task`。
- 用户对你的批评/表扬 → `edge(kind=feedback)`，必填 `feedback_category` 与 `valence`
  （批评负值 -0.6~-0.8，表扬正值 +0.6~+0.8）。
- 实体已存在于图中时用已有 `id`（先 `recall` 或 `status` 看不到全量时凭常识判断）。
- 无值得记的内容 → `{"nodes":[],"edges":[]}`。

## 与 markdown 记忆的关系（2026-09-11 变更，旧的「并行补充」说法已作废）

**图库是唯一真源，md 只是指针。** 用户 2026-09-11 裁定后已执行：

- 所有 md 记忆文件（`~/.workbuddy/MEMORY.md`、各工作区 `.workbuddy/memory/*.md`，共 71 个）
  **内容全部清空，改写成「指向图库」的指针文件**；
- 三个身份文件 `SOUL.md` / `USER.md` / `IDENTITY.md` **已删除**（它们本来也不进 agent 上下文）；
- 全量备份：`/Users/sai/WorkBuddy/memory-backup-20260911-1707.tar.gz`（84 个文件）
  与 `/Users/sai/WorkBuddy/identity+memory-backup-20260911-1710.tar.gz`（74 个文件）。回滚用 `tar -xzf <归档> -C /Users/sai`。

所以本层不再是「第三层」而是**唯一层**：用户偏好、项目脉络、反馈 valence、关系网络全在这里。
md 里那段指针只说明「去哪查」，本身不含任何事实。

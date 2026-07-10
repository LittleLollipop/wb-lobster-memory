# wb-lobster-memory

WorkBuddy 接入 [lobster-memory](https://github.com/LittleLollipop/lobster-memory) 长期图记忆的桥接技能。

作为 WorkBuddy 现有"云端 profile + 工作区 markdown"记忆**之外的并行补充层**，用知识图谱（实体-关系-情绪 valence）记录用户的偏好、项目脉络与反馈，支持按需回忆与定期巩固遗忘。抽取 JSON 由 WorkBuddy 自身兼任 LLM 生成（无平台 post-turn 钩子，靠惯例触发）。

## 文件

- `SKILL.md` — 技能说明、使用惯例、抽取 JSON schema
- `runner.py` — 命令行桥接脚本（status / remember / recall / feedback / should / consolidate）

## 前提

- 已安装并编译好的 [lobster-memory](https://github.com/LittleLollipop/lobster-memory)（底层 `axolotl_rs`）。
- `SKILL.md` 与 `runner.py` 中的路径**硬编码为作者本机**（`/Users/sai/.workbuddy/...`）。他人使用前需按自己的环境调整路径，或改为从环境变量读取。

## 用法

加载技能后见 `SKILL.md` 中的"WorkBuddy 使用惯例"。核心流程：

```
PY=/path/to/venvs/lobster-memory/bin/python
RUN=wb-lobster-memory/runner.py
$PY $RUN status                 # 会话起步：感知当前记忆规模
$PY $RUN remember --json '<抽取JSON>'   # 每轮有实质内容后落盘（WB 兼任 LLM 产出 JSON）
$PY $RUN recall <关键词>        # 按需回忆
$PY $RUN consolidate --round N  # 约每 20 轮或容量告警时巩固
```

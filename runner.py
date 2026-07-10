#!/usr/bin/env python3
"""WorkBuddy ↔ lobster-memory 桥接 runner。

把 lobster-memory 的 MemorySession 包成命令行，供 WorkBuddy 在对话中调用。
注意：抽取 JSON 由 WorkBuddy（兼任 LLM）自己生成，本脚本只负责落盘/回忆/巩固。

依赖：自带 axolotl_rs 的 lobster-memory venv 的 python（路径经 LOBSTER_MEMORY_ENGINE 等环境变量配置）
"""
import sys
import os
import json
import argparse

# 所有路径均可经环境变量覆盖；默认值指向作者本机布局。
# 他人使用前设置对应环境变量即可，无需改代码。
SKILL_ENGINE = os.environ.get(
    "LOBSTER_MEMORY_ENGINE", "/Users/sai/.workbuddy/skills/lobster-memory"
)
MEMORY_DIR = os.environ.get(
    "LOBSTER_MEMORY_DIR", os.path.expanduser("~/.workbuddy/lobster-memory")
)
MEMORY_PATH = os.path.join(MEMORY_DIR, "memory.axeb")
CONSOLIDATE_EVERY = int(os.environ.get("LOBSTER_MEMORY_CONSOLIDATE_EVERY", "20"))

sys.path.insert(0, SKILL_ENGINE)

try:
    from engine.integration import MemorySession  # noqa: E402
except ImportError as e:
    sys.stderr.write(
        "[wb-lobster-memory] 无法导入 lobster-memory 的 engine。\n"
        "  请确认 LOBSTER_MEMORY_ENGINE 指向含 engine/ 的目录，\n"
        "  且当前 python 所在 venv 已安装 axolotl_rs。\n"
        f"原始错误: {e}\n"
    )
    sys.exit(2)


def _session():
    os.makedirs(MEMORY_DIR, exist_ok=True)
    return MemorySession(MEMORY_PATH, consolidate_every=CONSOLIDATE_EVERY)


def cmd_status(_):
    s = _session()
    print(s.start())
    s.close()


def cmd_remember(args):
    raw = args.json if args.json else sys.stdin.read()
    raw = raw.strip()
    if not raw:
        print(json.dumps({"nodes_added": 0, "edges_added": 0, "error": "empty input"}, ensure_ascii=False))
        return
    s = _session()
    res = s.after_turn(raw)
    print(json.dumps(res, ensure_ascii=False))
    s.close()


def cmd_recall(args):
    s = _session()
    kws = args.keywords if args.keywords else None
    rows = s.recall(keywords=kws, domain=args.domain, limit=args.limit)
    if args.raw:
        print(json.dumps(rows, ensure_ascii=False, default=str))
    else:
        for m in rows:
            print(f"- {m.get('label')} | {m.get('content')} | domain={m.get('domain')} type={m.get('type')}")
    s.close()


def cmd_feedback(args):
    s = _session()
    rows = s.recall_feedback(valence=args.valence, limit=args.limit)
    if args.raw:
        print(json.dumps(rows, ensure_ascii=False, default=str))
    else:
        for m in rows:
            print(f"- {m.get('label')} | {m.get('content')} | valence={m.get('valence')}")
    s.close()


def cmd_should(args):
    s = _session()
    print(s.should_consolidate(args.round))
    s.close()


def cmd_consolidate(args):
    s = _session()
    if s.should_consolidate(args.round):
        s.consolidate()
        print(s.consolidate_summary())
    else:
        print("巩固未到期（容量未超且未到周期）")
    s.close()


def main():
    p = argparse.ArgumentParser(description="WorkBuddy lobster-memory bridge")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="打印当前记忆统计（注入会话上下文用）")

    pr = sub.add_parser("remember", help="写入一轮抽取结果")
    pr.add_argument("--json", help="抽取 JSON 字符串；缺省读 stdin")

    pc = sub.add_parser("recall", help="按需回忆")
    pc.add_argument("keywords", nargs="*", help="关键词")
    pc.add_argument("--domain", default=None, choices=["emotion", "knowledge", "task"])
    pc.add_argument("--limit", type=int, default=20)
    pc.add_argument("--raw", action="store_true", help="输出原始 JSON")

    pf = sub.add_parser("feedback", help="回忆历史反馈")
    pf.add_argument("--valence", default=None, choices=["positive", "negative"])
    pf.add_argument("--limit", type=int, default=20)
    pf.add_argument("--raw", action="store_true")

    ps = sub.add_parser("should", help="是否该巩固")
    ps.add_argument("--round", type=int, default=0)

    pcon = sub.add_parser("consolidate", help="执行巩固流水线")
    pcon.add_argument("--round", type=int, default=0)

    args = p.parse_args()
    {
        "status": cmd_status,
        "remember": cmd_remember,
        "recall": cmd_recall,
        "feedback": cmd_feedback,
        "should": cmd_should,
        "consolidate": cmd_consolidate,
    }[args.cmd](args)


if __name__ == "__main__":
    main()

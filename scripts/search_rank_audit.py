#!/usr/bin/env python3
"""Audit GitHub repository search rankings for this skill.

The script intentionally shells out to `gh search repos` so it uses the same
GitHub search surface a maintainer can reproduce locally.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass


TARGET_REPO = "B1lli/remove-ai-flavor-writing-skill"


@dataclass(frozen=True)
class Query:
    text: str
    group: str
    desired_rank: int | None = None


QUERIES = [
    Query("remove-ai-flavor-writing-skill", "exact", 1),
    Query("remove ai flavor writing skill", "exact", 1),
    Query("remove AI flavor", "exact", 1),
    Query("AI味清理", "exact", 1),
    Query("Chinese AI writing humanizer", "high-intent", 1),
    Query("去AI味 skill", "high-intent", 3),
    Query("去 AI 味 skill", "high-intent", 3),
    Query("去AI味 写作", "high-intent"),
    Query("中文去AI味", "high-intent"),
    Query("中文去 AI 味", "high-intent"),
    Query("降低AI感", "high-intent"),
    Query("降低 AIGC", "high-intent"),
    Query("AIGC 降低 skill", "high-intent"),
    Query("AI写作痕迹去除", "high-intent"),
    Query("AI 写作痕迹 去除", "high-intent"),
    Query("AI generated text Chinese humanizer", "english-long-tail"),
    Query("Chinese writing humanizer skill", "english-long-tail"),
    Query("Chinese text humanizer skill", "english-long-tail"),
    Query("Chinese AI text humanizer", "english-long-tail"),
    Query("remove AI writing patterns skill", "english-long-tail"),
    Query("AI writing humanizer skill", "english-long-tail"),
    Query("avoid AI writing skill", "english-long-tail"),
    Query("anti AI writing skill", "english-long-tail"),
    Query("anti AI slop writing skill", "english-long-tail"),
    Query("de AI writing skill", "competitor-adjacent"),
    Query("de-AI writing skill", "competitor-adjacent"),
    Query("humanizer zh", "competitor-adjacent"),
    Query("humanizer-zh alternative", "competitor-adjacent"),
    Query("Codex humanizer zh", "competitor-adjacent"),
    Query("Codex remove AI writing skill", "codex"),
    Query("Codex writing humanizer", "codex"),
    Query("Codex 去AI味 skill", "codex"),
    Query("Claude Code Chinese humanizer", "ecosystem"),
    Query("Claude Code 去AI味 skill", "ecosystem"),
    Query("OpenCode Chinese humanizer", "ecosystem"),
    Query("小红书 去AI味", "use-case"),
    Query("公众号 去AI味", "use-case"),
    Query("小说 去AI味 skill", "use-case"),
    Query("学术 写作 去AI味 skill", "use-case"),
    Query("论文 去AI味 skill", "use-case"),
]


def search(query: str, limit: int) -> list[dict]:
    command = [
        "gh",
        "search",
        "repos",
        query,
        "--limit",
        str(limit),
        "--json",
        "fullName,url,description,stargazersCount",
    ]
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        if "no repositories matched" in completed.stderr.lower() or not completed.stdout.strip():
            return []
        raise RuntimeError(f"GitHub search failed for {query!r}: {completed.stderr.strip()}")
    return json.loads(completed.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit GitHub search rank for target repo.")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of Markdown table")
    parser.add_argument("--fail-on-regression", action="store_true")
    args = parser.parse_args()

    rows = []
    failed = False
    for query in QUERIES:
        results = search(query.text, args.limit)
        names = [item["fullName"] for item in results]
        rank = names.index(TARGET_REPO) + 1 if TARGET_REPO in names else None
        top = names[:3]
        status = "tracked" if query.desired_rank is None else "pass"
        if query.desired_rank is not None:
            if rank is None or rank > query.desired_rank:
                status = "review"
                failed = True
        rows.append(
            {
                "query": query.text,
                "group": query.group,
                "desired_rank": query.desired_rank,
                "rank": rank,
                "status": status,
                "top_results": top,
            }
        )

    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print("| Group | Query | Desired | Rank | Status | Top results |")
        print("|---|---|---:|---:|---|---|")
        for row in rows:
            desired = row["desired_rank"] if row["desired_rank"] is not None else ""
            rank = row["rank"] if row["rank"] is not None else "not top 20"
            top = "<br>".join(row["top_results"])
            print(f"| {row['group']} | `{row['query']}` | {desired} | {rank} | {row['status']} | {top} |")

    return 1 if failed and args.fail_on_regression else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Lightweight regression audit for Chinese AI-flavor sentence shells."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Rule:
    rule_id: str
    label: str
    severity: int
    pattern: re.Pattern[str] | None = None
    terms: tuple[str, ...] = ()


RULES = [
    Rule(
        "binary_contrast",
        "二分对照壳",
        3,
        re.compile(r"(?:不是|并非|不在于|不只是|不止是|不仅是).{0,32}(?:而是|而在于|更是)|与其说.{0,32}不如说"),
    ),
    Rule(
        "staged_sequence",
        "机械先后顺序",
        2,
        re.compile(r"先.{0,24}(?:再|然后|后面|随后)|第一步.{0,60}第二步|从.{1,24}到.{1,24}"),
    ),
    Rule(
        "essence_claim",
        "真正/本质/核心式拔高",
        3,
        re.compile(r"真正.{0,24}(?:的是|在于|决定|重要|打动|改变)|本质上|核心在于|底层逻辑"),
    ),
    Rule(
        "assistant_route_marker",
        "助手路标词",
        3,
        terms=(
            "下面我们来",
            "接下来我会",
            "我们可以看到",
            "希望这能帮到你",
            "作为AI",
            "截至我的知识",
        ),
    ),
    Rule(
        "narrowing_frame",
        "过度收束开场",
        2,
        terms=(
            "这次只看",
            "今天只看",
            "这里只看",
            "我们只看",
        ),
    ),
    Rule(
        "easy_answer_colon",
        "很简单冒号模板",
        2,
        re.compile(r"[^。！？\n]{1,18}很简单[：:]"),
    ),
    Rule(
        "lecture_marker",
        "讲义腔/总结腔",
        2,
        terms=(
            "总的来说",
            "值得注意的是",
            "不可否认的是",
            "不难看出",
            "由此可见",
            "在这个过程中",
            "这背后其实",
            "说白了",
            "划重点",
            "捋一捋",
            "盘一盘",
            "拆一拆",
            "聊一聊",
        ),
    ),
    Rule(
        "inflated_abstract_words",
        "抽象包装词堆叠",
        1,
        terms=(
            "赋能",
            "助力",
            "抓手",
            "闭环",
            "深耕",
            "沉淀",
            "价值感",
            "长期主义",
            "意义深远",
            "前景广阔",
        ),
    ),
    Rule(
        "academic_filler",
        "学术/技术填充套话",
        2,
        re.compile(r"(?:基于|依据).{0,18}(?:理论|框架)|(?:研究表明|专家认为|业内普遍认为)|(?:综上所述|此案例(?:印证|揭示|说明)了|具有重要(?:理论|现实)?意义|提供了新思路|开辟了新方向)"),
    ),
    Rule(
        "rigid_enumeration",
        "整齐编号逻辑",
        2,
        re.compile(r"首先.{0,80}其次|其次.{0,80}(?:再次|最后)|一方面.{0,80}另一方面"),
    ),
    Rule(
        "fiction_cliche",
        "小说正文套话",
        1,
        terms=(
            "不禁",
            "情不自禁",
            "不由自主",
            "映入眼帘",
            "心中暗道",
            "暗自思忖",
            "嘴角微扬",
            "勾起一抹弧度",
            "脸色一变",
            "身形一顿",
            "缓缓说道",
            "淡淡地说",
        ),
    ),
]


def line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def excerpt(text: str, start: int, end: int) -> str:
    left = max(0, start - 24)
    right = min(len(text), end + 24)
    return text[left:right].replace("\n", "\\n")


def audit_text(text: str) -> dict:
    findings = []

    for rule in RULES:
        if rule.pattern:
            for match in rule.pattern.finditer(text):
                findings.append(
                    {
                        "rule": rule.rule_id,
                        "label": rule.label,
                        "severity": rule.severity,
                        "line": line_number(text, match.start()),
                        "match": match.group(0),
                        "excerpt": excerpt(text, match.start(), match.end()),
                    }
                )
        for term in rule.terms:
            start = 0
            while True:
                idx = text.find(term, start)
                if idx < 0:
                    break
                findings.append(
                    {
                        "rule": rule.rule_id,
                        "label": rule.label,
                        "severity": rule.severity,
                        "line": line_number(text, idx),
                        "match": term,
                        "excerpt": excerpt(text, idx, idx + len(term)),
                    }
                )
                start = idx + len(term)

    findings.extend(audit_shape(text))
    findings.sort(key=lambda item: (item["line"], -item["severity"], item["rule"]))
    score = sum(item["severity"] for item in findings)
    blockers = [item for item in findings if item["severity"] >= 3]
    return {
        "score": score,
        "finding_count": len(findings),
        "blocker_count": len(blockers),
        "status": "pass" if not blockers and score <= 2 else "review",
        "findings": findings,
    }


def audit_shape(text: str) -> list[dict]:
    findings: list[dict] = []
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    template_prefix = re.compile(
        r"^(?:概念|问题|原因|结论|答案|核心|本质|关键|目标|方法|步骤|第一步|第二步|第三步|SOP|"
        r"Hook|Usefulness|Specificity|Trust|Privacy|Tags|正文质量评分)"
        r"[：:]"
    )
    colon_lines = []
    for i, line in enumerate(lines, start=1):
        if template_prefix.match(line):
            colon_lines.append((i, line))
    if len(colon_lines) >= 3:
        findings.append(
            {
                "rule": "template_colon",
                "label": "冒号模板重复",
                "severity": 2,
                "line": colon_lines[0][0],
                "match": f"{len(colon_lines)} colon-template lines",
                "excerpt": " / ".join(line for _, line in colon_lines[:3]),
            }
        )

    sentences = [
        sentence.strip()
        for sentence in re.split(r"[。！？!?]\s*", text)
        if sentence.strip() and not sentence.strip().startswith("#")
    ]
    hen_judgments = [
        sentence
        for sentence in sentences
        if re.match(r"^[^，,；;：:\n]{1,18}很[^，,；;：:\n]{1,12}$", sentence)
    ]
    if len(hen_judgments) >= 3:
        findings.append(
            {
                "rule": "dense_hen_judgments",
                "label": "很字判断句过密",
                "severity": 2,
                "line": 1,
                "match": f"{len(hen_judgments)} 'X很X' sentences",
                "excerpt": " / ".join(hen_judgments[:3]),
            }
        )

    parallel_commas = re.findall(r"(?:[^，。！？\n]{2,18}很[^，。！？\n]{1,12}[，。]){3,}", text)
    if parallel_commas:
        first = parallel_commas[0]
        findings.append(
            {
                "rule": "parallel_hen_clauses",
                "label": "很字排比过密",
                "severity": 2,
                "line": line_number(text, text.find(first)),
                "match": "parallel '很' clauses",
                "excerpt": excerpt(text, text.find(first), text.find(first) + len(first)),
            }
        )

    paragraph_lengths = [
        len(re.sub(r"\s+", "", line))
        for line in text.split("\n\n")
        if line.strip() and not line.strip().startswith("#")
    ]
    medium_lengths = [length for length in paragraph_lengths if 24 <= length <= 90]
    if len(medium_lengths) >= 5 and max(medium_lengths) - min(medium_lengths) <= 12:
        findings.append(
            {
                "rule": "over_even_paragraph_distribution",
                "label": "段落长度过于均匀",
                "severity": 1,
                "line": 1,
                "match": f"paragraph lengths={medium_lengths[:8]}",
                "excerpt": "Vary paragraph weight; over-even distribution can look model-sorted.",
            }
        )

    final_line = next((line for line in reversed(lines) if not line.startswith("#")), "")
    if final_line.endswith(("？", "?")) and re.search(r"你|大家|有没有|是不是|觉得|卡在|哪一步", final_line):
        findings.append(
            {
                "rule": "ending_engagement_question",
                "label": "结尾假互动提问",
                "severity": 3,
                "line": max(1, len(text.splitlines())),
                "match": final_line,
                "excerpt": final_line,
            }
        )

    you_count = len(re.findall(r"你|大家", text))
    if you_count >= 6:
        findings.append(
            {
                "rule": "second_person_overuse",
                "label": "二人称过密",
                "severity": 1,
                "line": 1,
                "match": f"{you_count} second-person markers",
                "excerpt": "Use reader address only when the sentence genuinely speaks to the reader.",
            }
        )

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Chinese text for common AI-flavor shells.")
    parser.add_argument("paths", nargs="+", help="Markdown or text files to audit")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument("--fail-on-review", action="store_true", help="Exit 1 if any file needs review")
    args = parser.parse_args()

    results = {}
    failed = False
    for raw_path in args.paths:
        path = Path(raw_path)
        text = path.read_text(encoding="utf-8")
        result = audit_text(text)
        results[str(path)] = result
        failed = failed or result["status"] != "pass"

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for path, result in results.items():
            print(f"{path}: {result['status']} score={result['score']} findings={result['finding_count']} blockers={result['blocker_count']}")
            for item in result["findings"][:12]:
                print(f"  L{item['line']} [{item['label']}] {item['match']}")
            if len(result["findings"]) > 12:
                print(f"  ... {len(result['findings']) - 12} more")

    return 1 if args.fail_on_review and failed else 0


if __name__ == "__main__":
    sys.exit(main())

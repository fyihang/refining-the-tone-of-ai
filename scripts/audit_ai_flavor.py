#!/usr/bin/env python3
"""Audit Chinese prose for known AI-flavored writing patterns.

This is a regression aid, not an authorship detector or a prose-quality score.
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


PROFILES = ("general", "social", "academic", "fiction", "sop")
TEXT_SUFFIXES = {".md", ".markdown", ".txt"}
SENTENCE_BODY = r"[^\n。！？!?]"


@dataclass(frozen=True)
class Rule:
    rule_id: str
    label: str
    severity: int
    pattern: re.Pattern[str] | None = None
    terms: tuple[str, ...] = ()


RULES = (
    Rule(
        "binary_contrast",
        "二分对照壳",
        3,
        re.compile(
            rf"(?:不是|并非|不在于|不只是|不止是|不仅是){SENTENCE_BODY}{{0,32}}"
            rf"(?:而是|而在于|更是)|与其说{SENTENCE_BODY}{{0,32}}不如说"
        ),
    ),
    Rule(
        "staged_sequence",
        "机械先后顺序",
        2,
        re.compile(
            rf"先{SENTENCE_BODY}{{0,24}}(?:再|然后|后面|随后)|"
            rf"第一步{SENTENCE_BODY}{{0,60}}第二步"
        ),
    ),
    Rule(
        "essence_claim",
        "真正/本质/核心式拔高",
        3,
        re.compile(rf"真正{SENTENCE_BODY}{{0,24}}(?:的是|在于|决定|重要|打动|改变)|本质上|核心在于|底层逻辑"),
    ),
    Rule(
        "assistant_route_marker",
        "助手路标词",
        3,
        terms=("下面我们来", "接下来我会", "我们可以看到", "希望这能帮到你", "作为AI", "截至我的知识"),
    ),
    Rule("narrowing_frame", "过度收束开场", 2, terms=("这次只看", "今天只看", "这里只看", "我们只看")),
    Rule("easy_answer_colon", "很简单冒号模板", 2, re.compile(r"[^。！？!?\n]{1,18}很简单[：:]")),
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
        terms=("赋能", "助力", "抓手", "闭环", "深耕", "沉淀", "价值感", "长期主义", "意义深远", "前景广阔"),
    ),
    Rule(
        "academic_filler",
        "学术/技术填充套话",
        2,
        re.compile(
            r"(?:基于|依据)[^。！？!?\n]{0,18}(?:理论|框架)|"
            r"(?:研究表明|专家认为|业内普遍认为)|"
            r"(?:综上所述|此案例(?:印证|揭示|说明)了|具有重要(?:理论|现实)?意义|提供了新思路|开辟了新方向)"
        ),
    ),
    Rule(
        "rigid_enumeration",
        "整齐编号逻辑",
        2,
        re.compile(
            rf"首先{SENTENCE_BODY}{{0,80}}其次|其次{SENTENCE_BODY}{{0,80}}(?:再次|最后)|"
            rf"一方面{SENTENCE_BODY}{{0,80}}另一方面"
        ),
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
)


def line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def excerpt(text: str, start: int, end: int) -> str:
    left = max(0, start - 24)
    right = min(len(text), end + 24)
    return text[left:right].replace("\n", "\\n")


def protected_spans(text: str) -> list[tuple[int, int]]:
    spans = [(match.start(), match.end()) for match in re.finditer(r"```.*?```", text, re.DOTALL)]
    spans.extend((match.start(), match.end()) for match in re.finditer(r"`[^`\n]+`", text))
    return sorted(spans)


def quoted_spans(text: str) -> list[tuple[int, int]]:
    pattern = re.compile(r"“[^”\n]*”|‘[^’\n]*’|\"[^\"\n]*\"|'[^'\n]*'")
    return [(match.start(), match.end()) for match in pattern.finditer(text)]


def contained_in(start: int, end: int, spans: list[tuple[int, int]]) -> bool:
    return any(span_start <= start and end <= span_end for span_start, span_end in spans)


def is_exempt(
    rule_id: str,
    match_text: str,
    start: int,
    end: int,
    profile: str,
    protected: list[tuple[int, int]],
    quoted: list[tuple[int, int]],
) -> bool:
    if contained_in(start, end, protected):
        return True
    if contained_in(start, end, quoted):
        return True
    if profile == "academic" and rule_id == "essence_claim" and match_text == "核心在于":
        return True
    if profile == "sop" and rule_id in {"staged_sequence", "rigid_enumeration"}:
        return True
    return False


def finding(rule: Rule, text: str, start: int, end: int, match_text: str) -> dict:
    return {
        "rule": rule.rule_id,
        "label": rule.label,
        "severity": rule.severity,
        "line": line_number(text, start),
        "match": match_text,
        "excerpt": excerpt(text, start, end),
    }


def audit_text(text: str, profile: str = "general") -> dict:
    if profile not in PROFILES:
        raise ValueError(f"unsupported profile: {profile}")

    findings: list[dict] = []
    protected = protected_spans(text)
    quoted = quoted_spans(text)

    for rule in RULES:
        matches: list[tuple[int, int, str]] = []
        if rule.pattern:
            matches.extend((match.start(), match.end(), match.group(0)) for match in rule.pattern.finditer(text))
        for term in rule.terms:
            start = 0
            while True:
                index = text.find(term, start)
                if index < 0:
                    break
                matches.append((index, index + len(term), term))
                start = index + len(term)

        for start, end, match_text in matches:
            if not is_exempt(rule.rule_id, match_text, start, end, profile, protected, quoted):
                findings.append(finding(rule, text, start, end, match_text))

    findings.extend(audit_shape(text, sorted(protected + quoted)))
    findings.sort(key=lambda item: (item["line"], -item["severity"], item["rule"], item["match"]))
    score = sum(item["severity"] for item in findings)
    blockers = [item for item in findings if item["severity"] >= 3]
    return {
        "profile": profile,
        "score": score,
        "finding_count": len(findings),
        "blocker_count": len(blockers),
        "verdict": "review" if blockers or score > 2 else "clear",
        "findings": findings,
    }


def mask_spans(text: str, spans: list[tuple[int, int]]) -> str:
    characters = list(text)
    for start, end in spans:
        for index in range(start, end):
            if characters[index] != "\n":
                characters[index] = " "
    return "".join(characters)


def audit_shape(text: str, protected: list[tuple[int, int]]) -> list[dict]:
    findings: list[dict] = []
    visible_text = mask_spans(text, protected)
    nonempty_lines = [(number, line.strip()) for number, line in enumerate(visible_text.splitlines(), start=1) if line.strip()]

    template_prefix = re.compile(
        r"^(?:概念|问题|原因|结论|答案|核心|本质|关键|目标|方法|步骤|第一步|第二步|第三步|SOP|"
        r"Hook|Usefulness|Specificity|Trust|Privacy|Tags|正文质量评分)[：:]"
    )
    colon_lines = [(number, line) for number, line in nonempty_lines if template_prefix.match(line)]
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
        for sentence in re.split(r"[。！？!?]\s*", visible_text)
        if sentence.strip() and not sentence.strip().startswith("#")
    ]
    hen_judgments = [
        sentence for sentence in sentences if re.match(r"^[^，,；;：:\n]{1,18}很[^，,；;：:\n]{1,12}$", sentence)
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

    parallel_commas = re.findall(r"(?:[^，。！？\n]{2,18}很[^，。！？\n]{1,12}[，。]){3,}", visible_text)
    if parallel_commas:
        first = parallel_commas[0]
        start = visible_text.find(first)
        findings.append(
            {
                "rule": "parallel_hen_clauses",
                "label": "很字排比过密",
                "severity": 2,
                "line": line_number(visible_text, start),
                "match": "parallel '很' clauses",
                "excerpt": excerpt(visible_text, start, start + len(first)),
            }
        )

    paragraph_lengths = [
        len(re.sub(r"\s+", "", paragraph))
        for paragraph in visible_text.split("\n\n")
        if paragraph.strip() and not paragraph.strip().startswith("#")
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
                "excerpt": "Review whether repeated paragraph weight serves the text.",
            }
        )

    final_line_number, final_line = next(
        ((number, line) for number, line in reversed(nonempty_lines) if not line.startswith("#")),
        (1, ""),
    )
    if final_line.endswith(("？", "?")) and re.search(r"你|大家|有没有|是不是|觉得|卡在|哪一步", final_line):
        findings.append(
            {
                "rule": "ending_engagement_question",
                "label": "结尾假互动提问",
                "severity": 3,
                "line": final_line_number,
                "match": final_line,
                "excerpt": final_line,
            }
        )

    second_person_count = len(re.findall(r"你|大家", visible_text))
    if second_person_count >= 6:
        findings.append(
            {
                "rule": "second_person_overuse",
                "label": "二人称过密",
                "severity": 1,
                "line": 1,
                "match": f"{second_person_count} second-person markers",
                "excerpt": "Review whether each reader address is necessary.",
            }
        )

    return findings


def expand_input_paths(raw_paths: list[str]) -> list[Path]:
    expanded: list[Path] = []
    for raw_path in raw_paths:
        if glob.has_magic(raw_path):
            matches = [Path(match) for match in sorted(glob.glob(raw_path, recursive=True))]
            if not matches:
                raise ValueError(f"not found: {raw_path}")
            expanded.extend(path for path in matches if path.is_file())
            continue

        path = Path(raw_path)
        if path.is_dir():
            expanded.extend(
                child for child in sorted(path.iterdir()) if child.is_file() and child.suffix.lower() in TEXT_SUFFIXES
            )
        elif path.is_file():
            expanded.append(path)
        else:
            raise ValueError(f"not found: {raw_path}")

    unique: list[Path] = []
    seen: set[str] = set()
    for path in expanded:
        key = str(path.resolve())
        if key not in seen:
            unique.append(path)
            seen.add(key)
    if not unique:
        raise ValueError("no readable text files found")
    return unique


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Chinese prose for known AI-flavored patterns.")
    parser.add_argument("paths", nargs="*", help="Text files, directories, or glob patterns")
    parser.add_argument("--stdin", action="store_true", help="Read one document from standard input")
    parser.add_argument("--profile", choices=PROFILES, default="general")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument("--fail-on-review", action="store_true", help="Exit 1 if any document needs review")
    args = parser.parse_args()

    if args.stdin and args.paths:
        parser.error("--stdin cannot be combined with paths")
    if not args.stdin and not args.paths:
        parser.error("provide at least one path or use --stdin")

    try:
        if args.stdin:
            documents = [("<stdin>", sys.stdin.read())]
        else:
            documents = [(str(path), path.read_text(encoding="utf-8")) for path in expand_input_paths(args.paths)]
    except (OSError, UnicodeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    results = {name: audit_text(text, profile=args.profile) for name, text in documents}
    failed = any(result["verdict"] == "review" for result in results.values())

    if args.json:
        print(json.dumps({"schema_version": 1, "profile": args.profile, "results": results}, ensure_ascii=False, indent=2))
    else:
        for path, result in results.items():
            print(
                f"{path}: {result['verdict']} score={result['score']} "
                f"findings={result['finding_count']} blockers={result['blocker_count']} profile={result['profile']}"
            )
            for item in result["findings"][:12]:
                print(f"  L{item['line']} [{item['label']}] {item['match']}")
            if len(result["findings"]) > 12:
                print(f"  ... {len(result['findings']) - 12} more")

    return 1 if args.fail_on_review and failed else 0


if __name__ == "__main__":
    sys.exit(main())

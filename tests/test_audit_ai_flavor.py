from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_ROOT / "scripts" / "audit_ai_flavor.py"


def load_audit_module():
    spec = importlib.util.spec_from_file_location("tone_audit", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load audit module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


audit = load_audit_module()


class AuditBehaviorTests(unittest.TestCase):
    def test_general_profile_reviews_unnecessary_binary_shell(self):
        result = audit.audit_text("这不是效率问题，而是系统问题。", profile="general")
        self.assertEqual("review", result["verdict"])
        self.assertIn("binary_contrast", {item["rule"] for item in result["findings"]})

    def test_fiction_profile_preserves_required_dialogue(self):
        text = "沈弦说：“这不是参数波动，而是有人改了供电优先级。”"
        result = audit.audit_text(text, profile="fiction")
        self.assertEqual("clear", result["verdict"])
        self.assertNotIn("binary_contrast", {item["rule"] for item in result["findings"]})

    def test_direct_quote_is_not_treated_as_editable_prose(self):
        text = "报告原文写道：“这不是效率问题，而是系统问题。”"
        result = audit.audit_text(text, profile="general")
        self.assertEqual("clear", result["verdict"])
        self.assertNotIn("binary_contrast", {item["rule"] for item in result["findings"]})

    def test_academic_profile_does_not_block_defined_core_phrase(self):
        text = "该方法的核心在于保持边界条件一致。"
        result = audit.audit_text(text, profile="academic")
        self.assertEqual("clear", result["verdict"])
        essence = [item for item in result["findings"] if item["rule"] == "essence_claim"]
        self.assertEqual([1], [item["severity"] for item in essence])

    def test_academic_profile_reviews_core_phrase_when_other_filler_clusters(self):
        text = "本研究的核心在于赋能行业发展，具有重要现实意义。"
        result = audit.audit_text(text, profile="academic")
        self.assertEqual("review", result["verdict"])

    def test_sop_profile_allows_operational_order(self):
        text = "先关闭总闸，再拆下外壳。先确认电容放电，再接触主板。"
        result = audit.audit_text(text, profile="sop")
        self.assertEqual("clear", result["verdict"])
        sequences = [item for item in result["findings"] if item["rule"] == "staged_sequence"]
        self.assertEqual([0, 0], [item["severity"] for item in sequences])

    def test_sop_profile_reviews_ceremonial_sequence_with_jargon(self):
        text = "先统一思想，再形成共识。总的来说，这将赋能团队。"
        result = audit.audit_text(text, profile="sop")
        self.assertEqual("review", result["verdict"])

    def test_fiction_profile_reviews_clustered_narrator_cliches(self):
        text = "他不禁停下脚步，随后缓缓说道：夜已经深了。"
        result = audit.audit_text(text, profile="fiction")
        self.assertEqual("review", result["verdict"])

    def test_social_profile_reviews_clustered_marketing_jargon(self):
        text = "这套长期主义内容闭环会留下来。"
        result = audit.audit_text(text, profile="social")
        self.assertEqual("review", result["verdict"])

    def test_all_before_fixtures_require_review(self):
        fixture_dir = SKILL_ROOT / "tests" / "fixtures"
        verdicts = {
            path.name: audit.audit_text(path.read_text(encoding="utf-8"), profile="general")["verdict"]
            for path in fixture_dir.glob("*_before.md")
        }
        self.assertTrue(verdicts)
        self.assertEqual([], [name for name, verdict in verdicts.items() if verdict != "review"])

    def test_sequence_pattern_does_not_cross_sentence_boundary(self):
        text = "先关闭总闸。随后核对电压。"
        result = audit.audit_text(text, profile="general")
        self.assertNotIn("staged_sequence", {item["rule"] for item in result["findings"]})

    def test_fenced_code_is_not_audited_as_prose(self):
        text = "示例命令如下：\n```text\n先备份，再部署。\n```"
        result = audit.audit_text(text, profile="general")
        self.assertEqual("clear", result["verdict"])
        self.assertEqual([], result["findings"])

    def test_chinese_corner_quotes_are_not_treated_as_editable_prose(self):
        for text in (
            "报告写道：『这不是效率问题，而是系统问题。』",
            "报告写道：「这不是效率问题，\n而是系统问题。」",
        ):
            with self.subTest(text=text):
                result = audit.audit_text(text, profile="general")
                self.assertEqual("clear", result["verdict"])


class AuditCliTests(unittest.TestCase):
    def test_cli_expands_windows_style_glob(self):
        pattern = str(SKILL_ROOT / "tests" / "fixtures" / "*_after.md")
        completed = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), pattern, "--fail-on-review"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("academic_technical_after.md", completed.stdout)
        self.assertNotIn("Traceback", completed.stderr)

    def test_cli_accepts_stdin_and_emits_versioned_json(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--stdin", "--json", "--profile", "general"],
            input="普通句子。",
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(1, payload["schema_version"])
        self.assertEqual("clear", payload["results"]["<stdin>"]["verdict"])
        self.assertIn("not", payload["verdict_semantics"].lower())
        self.assertIn("authorship", payload["verdict_semantics"].lower())

    def test_cli_plain_output_explains_clear_verdict(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--stdin"],
            input="普通句子。",
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("not a prose-quality or authorship judgment", completed.stdout)

    def test_cli_reports_missing_path_without_traceback(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            missing = str(Path(temp_dir) / "missing.md")
            completed = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), missing],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        self.assertEqual(2, completed.returncode)
        self.assertIn("not found", completed.stderr.lower())
        self.assertNotIn("Traceback", completed.stderr)

    def test_cli_fail_on_review_exits_1_when_document_needs_review(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--stdin", "--fail-on-review"],
            input="这不是效率问题，而是系统问题。",
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(1, completed.returncode, completed.stdout + completed.stderr)
        self.assertIn("review", completed.stdout)
        self.assertNotIn("Traceback", completed.stderr)


def rules_of(result):
    return {item["rule"] for item in result["findings"]}


class AuditBoundaryRegressionTests(unittest.TestCase):
    def test_xian_inside_common_words_is_not_staged_sequence(self):
        for text in (
            "王先生再次来电确认了时间。",
            "系统会优先处理队列，再写日志。",
            "事先通知相关人，再开始变更。",
            "首先核对名单，再发放材料。",
            "他率先到达现场，再组织分工。",
            "预先准备材料，再进场。",
            "抢先发布通知，再补说明。",
        ):
            with self.subTest(text=text):
                result = audit.audit_text(text, profile="general")
                self.assertNotIn("staged_sequence", rules_of(result))

    def test_real_staged_sequence_still_matches(self):
        for text in (
            "先关闭总闸，再拆下外壳。",
            "我会先整理资料，再输出方案。",
            "先生先到，再登记。",
            "第一步备份配置，第二步开放流量。",
        ):
            with self.subTest(text=text):
                result = audit.audit_text(text, profile="general")
                sequences = [item for item in result["findings"] if item["rule"] == "staged_sequence"]
                self.assertEqual([2], [item["severity"] for item in sequences])

    def test_false_contrast_shells_do_not_match(self):
        for text in (
            "要不是下雨，而是晴天，比赛也会照常。",
            "你是不是把附件发错了，而是发到了旧邮箱。",
        ):
            with self.subTest(text=text):
                result = audit.audit_text(text, profile="general")
                self.assertNotIn("binary_contrast", rules_of(result))

    def test_real_binary_contrast_still_matches_at_severity_3(self):
        text = "你是不是觉得这不是效率问题，而是系统问题。"
        result = audit.audit_text(text, profile="general")
        contrasts = [item for item in result["findings"] if item["rule"] == "binary_contrast"]
        self.assertEqual(1, len(contrasts))
        self.assertEqual(3, contrasts[0]["severity"])
        self.assertIn("不是效率问题，而是", contrasts[0]["match"])

    def test_adjacent_contrasts_are_counted_separately(self):
        text = "不是记录问题，而是交接问题；不是个人疏忽，而是名单过期。"
        result = audit.audit_text(text, profile="general")
        contrasts = [item for item in result["findings"] if item["rule"] == "binary_contrast"]
        self.assertEqual(2, len(contrasts))
        self.assertEqual([3, 3], [item["severity"] for item in contrasts])

    def test_missing_contrast_forms_are_detected(self):
        samples = (
            "问题不在这段脚本里，而在昨天改过的配置。",
            "预算并没有增加，而是改了支出科目。",
        )
        for text in samples:
            with self.subTest(text=text):
                result = audit.audit_text(text, profile="general")
                contrasts = [item for item in result["findings"] if item["rule"] == "binary_contrast"]
                self.assertEqual([3], [item["severity"] for item in contrasts])

    def test_existing_contrast_forms_still_match_once(self):
        for text in (
            "不在于形式，而在于结果。",
            "不只是记录，更是复盘。",
            "并非临时起意，而是长期安排。",
            "与其说是效率问题，不如说是系统问题。",
        ):
            with self.subTest(text=text):
                result = audit.audit_text(text, profile="general")
                contrasts = [item for item in result["findings"] if item["rule"] == "binary_contrast"]
                self.assertEqual(1, len(contrasts))
                self.assertEqual(3, contrasts[0]["severity"])

    def test_partial_quote_does_not_exempt_surrounding_contrast(self):
        text = "他说的不是“效率”，而是“系统”。"
        result = audit.audit_text(text, profile="general")
        self.assertIn("binary_contrast", rules_of(result))

    def test_jin_and_zhuli_do_not_match_longer_words(self):
        banned = audit.audit_text("本场所不禁止拍照。", profile="general")
        self.assertNotIn("fiction_cliche", rules_of(banned))
        vehicle = audit.audit_text("电动助力车停在门口。", profile="general")
        self.assertNotIn("inflated_abstract_words", rules_of(vehicle))

    def test_jin_and_zhuli_still_match_as_terms(self):
        cliche = audit.audit_text("他不禁停下脚步。", profile="fiction")
        hits = [item for item in cliche["findings"] if item["rule"] == "fiction_cliche"]
        self.assertEqual([("不禁", 2)], [(item["match"], item["severity"]) for item in hits])

        mixed = audit.audit_text("规定不禁止旁听，他不禁笑出声。", profile="general")
        hits = [item for item in mixed["findings"] if item["rule"] == "fiction_cliche"]
        self.assertEqual(["不禁"], [item["match"] for item in hits])

        help_word = audit.audit_text("这项安排会助力后续复盘。", profile="general")
        hits = [item for item in help_word["findings"] if item["rule"] == "inflated_abstract_words"]
        self.assertEqual([("助力", 1)], [(item["match"], item["severity"]) for item in hits])

        both = audit.audit_text("购买助力车之后，再谈如何助力复盘。", profile="general")
        hits = [item for item in both["findings"] if item["rule"] == "inflated_abstract_words"]
        self.assertEqual(["助力"], [item["match"] for item in hits])

    def test_qingbuzijin_is_not_also_counted_as_bujin(self):
        result = audit.audit_text("她情不自禁地笑了。", profile="general")
        hits = [item for item in result["findings"] if item["rule"] == "fiction_cliche"]
        self.assertEqual(["情不自禁"], [item["match"] for item in hits])


class AuditQuoteAndTitleRegressionTests(unittest.TestCase):
    def test_unclosed_quote_does_not_exempt_later_paragraphs(self):
        text = (
            "草稿开头落下一个“。\n"
            "\n"
            "总的来说，这不是效率问题，而是系统问题。真正重要的是把边界写清楚。\n"
            "\n"
            "写到这里才补上收尾的”。\n"
        )
        result = audit.audit_text(text, profile="general")
        self.assertIn("lecture_marker", rules_of(result))
        self.assertIn("binary_contrast", rules_of(result))
        self.assertIn("essence_claim", rules_of(result))

    def test_blank_line_of_spaces_also_ends_quote_span(self):
        text = "句首有一个“。\n \n总的来说，这不是效率问题，而是系统问题。\n \n结束的”。"
        result = audit.audit_text(text, profile="general")
        self.assertIn("lecture_marker", rules_of(result))
        self.assertIn("binary_contrast", rules_of(result))

    def test_quote_may_still_cross_a_single_line_break(self):
        text = "报告写道：「这不是效率问题，\n而是系统问题。」"
        result = audit.audit_text(text, profile="general")
        self.assertNotIn("binary_contrast", rules_of(result))
        self.assertEqual("clear", result["verdict"])

    def test_ascii_apostrophes_do_not_exempt_prose(self):
        text = "It's fine. 这不是效率问题，而是系统问题。 Don't worry."
        result = audit.audit_text(text, profile="general")
        contrasts = [item for item in result["findings"] if item["rule"] == "binary_contrast"]
        self.assertEqual(1, len(contrasts))
        self.assertEqual(3, contrasts[0]["severity"])

    def test_ascii_single_quotes_around_chinese_still_exempt(self):
        text = "他说：'这不是效率问题，而是系统问题。'"
        result = audit.audit_text(text, profile="general")
        self.assertNotIn("binary_contrast", rules_of(result))

    def test_book_title_marks_are_not_audited(self):
        titled = audit.audit_text("详见《先备份，再部署》里的说明。", profile="general")
        self.assertNotIn("staged_sequence", rules_of(titled))
        titled_term = audit.audit_text("请阅读《赋能团队的方法》。", profile="general")
        self.assertNotIn("inflated_abstract_words", rules_of(titled_term))

    def test_text_outside_book_title_marks_is_still_audited(self):
        result = audit.audit_text("先备份配置，再阅读《部署手册》。", profile="general")
        sequences = [item for item in result["findings"] if item["rule"] == "staged_sequence"]
        self.assertEqual(1, len(sequences))
        outside = audit.audit_text("这套做法会赋能团队，详见《手册》。", profile="general")
        words = [item for item in outside["findings"] if item["rule"] == "inflated_abstract_words"]
        self.assertEqual(["赋能"], [item["match"] for item in words])


class AuditCitationAndQuestionRegressionTests(unittest.TestCase):
    def test_research_claim_with_nearby_citation_is_skipped(self):
        for text in (
            "研究表明，注意力会回升（Chen, 2020）。",
            "研究表明，注意力会回升（林某，2019）。",
            "研究表明该方法有效[12]。",
            "研究表明该方法有效(Chen, 2020)。",
            "研究表明" + ("补" * 29) + "（Ada, 2020）。",
        ):
            with self.subTest(text=text):
                result = audit.audit_text(text, profile="academic")
                self.assertNotIn("academic_filler", rules_of(result))

    def test_research_claim_without_nearby_citation_still_matches(self):
        for text in (
            "研究表明，注意力会回升。",
            "研究表明[待补]。",
            "研究表明" + ("补" * 30) + "（Ada, 2020）。",
            "专家认为这种方法可行（Chen, 2020）。",
        ):
            with self.subTest(text=text):
                result = audit.audit_text(text, profile="academic")
                fillers = [item for item in result["findings"] if item["rule"] == "academic_filler"]
                self.assertEqual([2], [item["severity"] for item in fillers])

    def test_transactional_closing_questions_are_skipped(self):
        for text in (
            "请问你周四下午三点前能确认参会人数吗？",
            "你能否参加这次讨论吗？",
            "你方便看一下附件吗？",
            "你知道截止日期改了吗？",
            "你收到后确认一下参会人数吗？",
            "请问你还有补充吗？",
            "你周四有空吗？",
            "你三点前有空吗？",
        ):
            with self.subTest(text=text):
                result = audit.audit_text(text, profile="general")
                self.assertNotIn("ending_engagement_question", rules_of(result))

    def test_generic_closing_questions_still_match(self):
        for text in (
            "你觉得这个方案怎么样？",
            "大家还有没有想补充的？",
            "你有一点想法吗？",
        ):
            with self.subTest(text=text):
                result = audit.audit_text(text, profile="general")
                questions = [item for item in result["findings"] if item["rule"] == "ending_engagement_question"]
                self.assertEqual([3], [item["severity"] for item in questions])


class AuditShapeLineAndRecursiveTests(unittest.TestCase):
    def test_shape_rules_report_real_line_numbers(self):
        hen = audit.audit_text("前言一句。\n\n房间很暗。风很大。路很滑。", profile="general")
        hen_hits = [item for item in hen["findings"] if item["rule"] == "dense_hen_judgments"]
        self.assertEqual([3], [item["line"] for item in hen_hits])

        paragraphs = "标题\n\n" + "\n\n".join(["段" * 30] * 5)
        even = audit.audit_text(paragraphs, profile="general")
        even_hits = [item for item in even["findings"] if item["rule"] == "over_even_paragraph_distribution"]
        self.assertEqual([3], [item["line"] for item in even_hits])

        people = audit.audit_text(
            "这里没有称呼。\n\n你看看甲，你看看乙，你看看丙，大家看看丁，你看看戊，大家看看己。",
            profile="general",
        )
        people_hits = [item for item in people["findings"] if item["rule"] == "second_person_overuse"]
        self.assertEqual([3], [item["line"] for item in people_hits])

    def test_cli_directory_scan_is_not_recursive_by_default(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            nested = root / "nested"
            nested.mkdir()
            (nested / "note.md").write_text("普通句子。", encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), str(root)],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        self.assertEqual(2, completed.returncode)
        self.assertIn("no readable text files", completed.stderr.lower())
        self.assertNotIn("Traceback", completed.stderr)

    def test_cli_recursive_flag_scans_subdirectories(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            nested = root / "nested"
            nested.mkdir()
            (root / "top.txt").write_text("普通句子。", encoding="utf-8")
            (nested / "note.md").write_text("这也是普通句子。", encoding="utf-8")
            (nested / "skip.py").write_text("print('先备份，再部署')", encoding="utf-8")
            without = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), str(root), "--json"],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            with_flag = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), str(root), "--recursive", "--json"],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        self.assertEqual(0, without.returncode, without.stderr)
        without_payload = json.loads(without.stdout)
        self.assertEqual(["top.txt"], [Path(name).name for name in without_payload["results"]])
        self.assertEqual(0, with_flag.returncode, with_flag.stderr)
        with_payload = json.loads(with_flag.stdout)
        self.assertEqual(
            ["note.md", "top.txt"],
            sorted(Path(name).name for name in with_payload["results"]),
        )
        self.assertEqual(1, with_payload["schema_version"])
        self.assertNotIn("skip.py", with_flag.stdout)


if __name__ == "__main__":
    unittest.main()

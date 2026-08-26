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


if __name__ == "__main__":
    unittest.main()

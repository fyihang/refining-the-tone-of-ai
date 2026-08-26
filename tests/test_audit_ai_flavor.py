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

    def test_academic_profile_does_not_block_defined_core_phrase(self):
        text = "该方法的核心在于保持边界条件一致。"
        result = audit.audit_text(text, profile="academic")
        self.assertEqual("clear", result["verdict"])
        self.assertNotIn("essence_claim", {item["rule"] for item in result["findings"]})

    def test_sop_profile_allows_operational_order(self):
        text = "先关闭总闸，再拆下外壳。先确认电容放电，再接触主板。"
        result = audit.audit_text(text, profile="sop")
        self.assertEqual("clear", result["verdict"])
        self.assertNotIn("staged_sequence", {item["rule"] for item in result["findings"]})

    def test_sequence_pattern_does_not_cross_sentence_boundary(self):
        text = "先关闭总闸。随后核对电压。"
        result = audit.audit_text(text, profile="general")
        self.assertNotIn("staged_sequence", {item["rule"] for item in result["findings"]})

    def test_fenced_code_is_not_audited_as_prose(self):
        text = "示例命令如下：\n```text\n先备份，再部署。\n```"
        result = audit.audit_text(text, profile="general")
        self.assertEqual("clear", result["verdict"])
        self.assertEqual([], result["findings"])


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

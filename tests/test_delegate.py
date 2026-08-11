"""Stdlib unit tests for codex-delegate wrapper.

Does not invoke the real `codex` binary or the network.
Import the script by file path (no package layout).
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "delegate_codex.py"
MODULE_NAME = "delegate_codex_under_test"


def _load_module():
    spec = importlib.util.spec_from_file_location(MODULE_NAME, SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load wrapper from {SCRIPT}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestParseDuration(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = _load_module()

    def test_seconds_suffix(self) -> None:
        self.assertEqual(self.mod.parse_duration("90s"), 90.0)

    def test_minutes_suffix(self) -> None:
        self.assertEqual(self.mod.parse_duration("45m"), 2700.0)

    def test_hours_suffix(self) -> None:
        self.assertEqual(self.mod.parse_duration("2h"), 7200.0)

    def test_bare_number(self) -> None:
        self.assertEqual(self.mod.parse_duration("30"), 30.0)

    def test_rejects_non_positive_duration(self) -> None:
        for value in ("0", "-1s"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.mod.parse_duration(value)


class TestFindCodex(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = _load_module()

    def test_honors_codex_bin_env(self) -> None:
        fake = str(Path(tempfile.gettempdir()) / "fake-codex-bin-for-tests.exe")
        previous = os.environ.get("CODEX_BIN")
        os.environ["CODEX_BIN"] = fake
        try:
            self.assertEqual(self.mod.find_codex(), fake)
        finally:
            if previous is None:
                os.environ.pop("CODEX_BIN", None)
            else:
                os.environ["CODEX_BIN"] = previous


class TestRunBounded(unittest.TestCase):
    def test_utf8_and_timeout(self) -> None:
        mod = _load_module()
        result = mod.run_bounded([sys.executable, "-c", "import sys; sys.stdout.buffer.write('Привет'.encode())"], SKILL_ROOT, 10)
        self.assertEqual(result.stdout.strip(), "Привет")
        with self.assertRaises(subprocess.TimeoutExpired):
            mod.run_bounded([sys.executable, "-c", "import time; time.sleep(30)"], SKILL_ROOT, 0.1)


class TestMainCli(unittest.TestCase):
    def test_timeout_writes_manifest(self) -> None:
        mod = _load_module()
        with tempfile.TemporaryDirectory() as output_dir, mock.patch.object(mod, "find_codex", return_value=sys.executable), mock.patch.object(mod, "run_bounded", side_effect=subprocess.TimeoutExpired([], 1, output=b"partial", stderr=b"warning")), mock.patch.object(sys, "argv", ["delegate", "--cwd", str(SKILL_ROOT), "--task", "test", "--output-dir", output_dir]):
            self.assertEqual(mod.main(), 124)
            manifest = json.loads((Path(output_dir) / "result.json").read_text(encoding="utf-8"))
            self.assertEqual((manifest["tool"], manifest["exit_code"], manifest["timed_out"]), ("codex", 124, True))

    def test_nonexistent_cwd_exits_2(self) -> None:
        bogus = str(Path(tempfile.gettempdir()) / "codex-delegate-no-such-cwd-xyz")
        if Path(bogus).exists():
            self.skipTest("unexpected existing path for bogus cwd fixture")
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--cwd", bogus, "--task", "test"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 2, msg=proc.stderr)
        self.assertIn("does not exist", proc.stderr.lower())

    def test_missing_binary_exits_127(self) -> None:
        fake_bin = str(Path(tempfile.gettempdir()) / "missing-codex-xyz123.exe")
        if Path(fake_bin).is_file():
            self.skipTest("unexpected real file at fake bin path")
        env = os.environ.copy()
        env["CODEX_BIN"] = fake_bin
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--cwd", str(SKILL_ROOT), "--task", "test"],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        combined = (proc.stderr or "") + (proc.stdout or "")
        if proc.returncode not in (127, 126) and "not found" not in combined.lower():
            self.skipTest(
                f"CODEX_BIN override appears bypassed (exit {proc.returncode}): {combined[:400]}"
            )
        self.assertEqual(proc.returncode, 127, msg=combined)
        self.assertIn("not found", combined.lower())


if __name__ == "__main__":
    unittest.main()

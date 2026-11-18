"""Tests for tools/build_directory_edition.py (the Claude plugin directory edition).

Run from the repository root:  python3 -m unittest discover tests
"""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import build_directory_edition as bde  # noqa: E402

SOURCE = ROOT / "plugins" / "spring-api-validator"


class DirectoryEditionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "edition"
        with contextlib.redirect_stdout(io.StringIO()):
            cls.status = bde.main(["--out", str(cls.out)])
        cls.plugin = cls.out / "plugins" / "spring-api-validator"

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def files(self, base):
        return {p.relative_to(base).as_posix() for p in base.rglob("*") if p.is_file()
                and "scripts" not in p.relative_to(base).parts and p.name != ".DS_Store"
                and "__pycache__" not in p.parts}

    def test_build_passes_its_own_checks(self):
        self.assertEqual(self.status, 0)
        self.assertEqual(bde.check(self.out), [])

    def test_scripts_are_left_out_and_everything_else_is_kept(self):
        self.assertFalse(list(self.out.rglob("scripts")))
        self.assertFalse(list(self.out.rglob("*.py")))
        self.assertEqual(self.files(self.plugin), self.files(SOURCE))

    def test_no_file_starts_with_a_shebang(self):
        for p in self.out.rglob("*"):
            if p.is_file():
                self.assertFalse(p.read_bytes().startswith(b"#!"), p)

    def test_manifest_keeps_identity_and_drops_script_claims(self):
        src = json.loads((SOURCE / ".claude-plugin" / "plugin.json").read_text())
        out = json.loads((self.plugin / ".claude-plugin" / "plugin.json").read_text())
        for key in ("name", "version", "icon", "author", "license", "repository"):
            self.assertEqual(out[key], src[key], key)
        self.assertNotIn("checker", out["description"])
        self.assertNotIn("GitHub Action", out["description"])
        self.assertNotIn("github-action", out["keywords"])

    def test_readme_is_the_directory_one(self):
        readme = (self.plugin / "README.md").read_text()
        self.assertEqual(readme, (ROOT / "directory" / "README.md").read_text())
        self.assertNotIn("quick_check", readme)
        self.assertGreaterEqual(len(readme.split()), 40)

    def test_skills_explain_what_to_do_without_scripts(self):
        main = (self.plugin / "skills" / "spring-api-validator" / "SKILL.md").read_text()
        self.assertIn("Without `scripts/`", main)
        command = (self.plugin / "skills" / "validate-api" / "SKILL.md").read_text()
        self.assertIn("Without it, do the mechanical checks by hand", command)

    def test_check_catches_forbidden_files(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "run.sh").write_text("echo hi\n")
            (d / "notes.md").write_text("#!/bin/sh\necho hi\n")
            (d / "bad.json").write_text("{")
            problems = "\n".join(bde.check(d))
        self.assertIn("run.sh: file type not allowed", problems)
        self.assertIn("notes.md: starts with #!", problems)
        self.assertIn("bad.json: invalid JSON", problems)

    def test_refuses_to_replace_an_unrelated_folder(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "keep.txt").write_text("mine")
            with self.assertRaises(SystemExit):
                bde.build(Path(d))
            self.assertTrue((Path(d) / "keep.txt").exists())


if __name__ == "__main__":
    unittest.main()

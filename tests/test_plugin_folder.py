"""Keep the plugin folder within the Claude plugin directory's rules for unverified publishers.

Only Markdown, text, JSON, YAML and raster images; no file starting with "#!"; UTF-8 text;
nothing over the 256 KiB review limit. The standalone checker lives in checker/, outside it.
Run from the repository root:  python3 -m unittest discover tests
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugins" / "spring-api-validator"

ALLOWED_SUFFIXES = {".md", ".txt", ".json", ".yaml", ".yml", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico"}
ALLOWED_NAMES = {"LICENSE"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico"}
IGNORED = {".DS_Store"}
MAX_BYTES = 256 * 1024


def plugin_files():
    return sorted(p for p in PLUGIN.rglob("*")
                  if p.is_file() and p.name not in IGNORED and "__pycache__" not in p.parts)


class PluginFolderTest(unittest.TestCase):
    def test_only_allowed_file_types(self):
        for p in plugin_files():
            with self.subTest(p.relative_to(PLUGIN).as_posix()):
                self.assertTrue(p.suffix.lower() in ALLOWED_SUFFIXES or p.name in ALLOWED_NAMES)

    def test_no_shebangs_valid_utf8_and_small(self):
        for p in plugin_files():
            rel = p.relative_to(PLUGIN).as_posix()
            data = p.read_bytes()
            with self.subTest(rel):
                self.assertLessEqual(len(data), MAX_BYTES)
                if p.suffix.lower() in IMAGE_SUFFIXES:
                    continue
                self.assertFalse(data.startswith(b"#!"))
                text = data.decode("utf-8")
                if p.suffix == ".json":
                    json.loads(text)

    def test_skills_and_readme_do_not_point_at_missing_scripts(self):
        for p in plugin_files():
            if p.suffix == ".md":
                text = p.read_text(encoding="utf-8")
                with self.subTest(p.relative_to(PLUGIN).as_posix()):
                    self.assertNotIn("scripts/", text)
                    self.assertNotIn("quick_check.py", text)

    def test_readme_long_enough_and_versions_match(self):
        readme = (PLUGIN / "README.md").read_text(encoding="utf-8")
        self.assertGreaterEqual(len(readme.split()), 40)
        plugin = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())
        market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
        self.assertEqual(plugin["version"], market["plugins"][0]["version"])


if __name__ == "__main__":
    unittest.main()

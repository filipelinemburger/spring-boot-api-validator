"""Build the Claude plugin directory edition of the plugin.

The directory accepts only Markdown, text, JSON, YAML and raster images from unverified
organizations, and no file that starts with "#!". This edition is the plugin folder without
the skills' scripts/ directories (the skill falls back to doing those checks by reading the
code), with a README and description that don't claim the scripts.

Usage: python3 tools/build_directory_edition.py --out <dir>
Writes <dir>/plugins/spring-api-validator plus a root README.md and LICENSE, then checks
every file against the directory's rules. Exits 1 if a check fails.
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = "plugins/spring-api-validator"
SOURCE = ROOT / PLUGIN

DESCRIPTION = (
    "Review Spring Boot REST APIs (Java or Kotlin, MVC or WebFlux) for real defects: HTTP verb "
    "and status semantics, parameter binding, Bean Validation, DTOs and Jackson, error handling, "
    "resource ownership, database column limits and OpenAPI contract drift. Includes a "
    "/validate-api command for branches and pull requests."
)
DROP_KEYWORDS = {"github-action"}

ALLOWED_SUFFIXES = {".md", ".txt", ".json", ".yaml", ".yml", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico"}
ALLOWED_NAMES = {"LICENSE"}  # extensionless text
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico"}
MAX_BYTES = 256 * 1024
SKIP_NAMES = {".DS_Store", "__pycache__"}

ROOT_README = """# spring-api-validator — directory edition

Generated from `main` by `tools/build_directory_edition.py`; don't edit this branch by hand.
It holds the Claude plugin directory edition of the plugin in `plugins/spring-api-validator`:
the same skills and references without the bundled Python scripts. The full plugin, the
standalone checker and the GitHub Action live on the `main` branch.
"""


def ignore(directory, names):
    skipped = {n for n in names if n in SKIP_NAMES or n.endswith(".pyc")}
    # skills/<skill>/scripts
    if Path(directory).parent.name == "skills":
        skipped |= {n for n in names if n == "scripts"}
    return skipped


def build(out: Path) -> Path:
    if out.exists():
        previous = out / "README.md"
        leftovers = [p for p in out.iterdir() if p.name != ".git"]
        if leftovers and not (previous.is_file() and "directory edition" in previous.read_text(encoding="utf-8", errors="replace")):
            raise SystemExit(f"refusing to replace {out}: not empty and not a previous directory edition")
        for p in leftovers:  # keep .git so the output can be a checkout of the directory branch
            shutil.rmtree(p) if p.is_dir() else p.unlink()
        out.mkdir(exist_ok=True)
    else:
        out.mkdir(parents=True)
    target = out / PLUGIN
    shutil.copytree(SOURCE, target, ignore=ignore)

    shutil.copyfile(ROOT / "directory" / "README.md", target / "README.md")

    manifest_path = target / ".claude-plugin" / "plugin.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["description"] = DESCRIPTION
    manifest["keywords"] = [k for k in manifest.get("keywords", []) if k not in DROP_KEYWORDS]
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    (out / "README.md").write_text(ROOT_README, encoding="utf-8")
    shutil.copyfile(ROOT / "LICENSE", out / "LICENSE")
    return target


def check(out: Path) -> list:
    problems = []
    for path in sorted(p for p in out.rglob("*") if p.is_file() and ".git" not in p.relative_to(out).parts):
        rel = path.relative_to(out).as_posix()
        suffix = path.suffix.lower()
        if suffix not in ALLOWED_SUFFIXES and path.name not in ALLOWED_NAMES:
            problems.append(f"{rel}: file type not allowed")
            continue
        data = path.read_bytes()
        if len(data) > MAX_BYTES:
            problems.append(f"{rel}: {len(data)} bytes, over the {MAX_BYTES}-byte review limit")
        if suffix in IMAGE_SUFFIXES:
            continue
        if data.startswith(b"#!"):
            problems.append(f"{rel}: starts with #!")
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            problems.append(f"{rel}: not valid UTF-8")
            continue
        if suffix == ".json":
            try:
                json.loads(text)
            except ValueError as e:
                problems.append(f"{rel}: invalid JSON ({e})")
        if "scripts/" in text and rel.endswith("/README.md"):
            problems.append(f"{rel}: README mentions scripts/")
    if list(out.rglob("scripts")):
        problems.append("a scripts/ directory is still present")
    return problems


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", required=True, type=Path, help="output directory (replaced)")
    args = ap.parse_args(argv)
    out = args.out.resolve()
    if out == ROOT or ROOT in out.parents and out.parts[len(ROOT.parts)] in {"plugins", ".git"}:
        ap.error("--out must not be inside the repository's plugin or .git folders")
    target = build(out)
    problems = check(out)
    for p in problems:
        print(f"error: {p}", file=sys.stderr)
    if problems:
        return 1
    files = sum(1 for p in out.rglob("*") if p.is_file() and ".git" not in p.relative_to(out).parts)
    print(f"Directory edition built at {target} ({files} files); all files pass the directory rules.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

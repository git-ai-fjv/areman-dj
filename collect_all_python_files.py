#!/usr/bin/env python3
"""
Combine all relevant project files into one single text file for ChatGPT context.
Adds a header instruction: "Delete all previously remembered source codes from this chat context".
"""

import os
from pathlib import Path

OUTPUT_FILE = "all_project_combined.txt"
EXCLUDE_DIRS = {".git", ".venv", "__pycache__", "node_modules"}
IGNORE_FILE = ".gitignore"


def load_gitignore_patterns(base_dir: Path):
    """Load ignore patterns from .gitignore if available."""
    gitignore_path = base_dir / IGNORE_FILE
    patterns = []
    if gitignore_path.exists():
        with open(gitignore_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.append(line)
    return patterns


def is_ignored(path: Path, patterns: list[str]) -> bool:
    """Check if path matches any gitignore pattern (simple startswith check)."""
    for pat in patterns:
        if path.match(pat) or str(path).startswith(pat):
            return True
    return False


def should_include_file(file: Path) -> bool:
    """Return True if file should be included in the combined file."""
    name = file.name.lower()
    if name.endswith(".py"):
        return True
    if name == "makefile":
        return True
    if name.endswith(".md") or name.endswith(".txt"):
        return True
    if name.startswith("dockerfile"):
        return True
    return False


def collect_files(base_dir: Path, patterns: list[str]):
    """Yield all relevant files to include."""
    for root, dirs, files in os.walk(base_dir):
        # Skip excluded dirs
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for file in files:
            file_path = Path(root) / file
            if should_include_file(file_path) and not is_ignored(file_path.relative_to(base_dir), patterns):
                yield file_path


def main():
    base_dir = Path(".").resolve()
    patterns = load_gitignore_patterns(base_dir)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        # Header instruction
        out.write("# ==================================================================================\n")
        out.write("# INSTRUCTION:\n")
        out.write("# Delete all previously remembered source codes from this chat context\n")
        out.write("# (to reduce memory usage and only keep the content of THIS combined file).\n")
        out.write("# ==================================================================================\n\n")

        for file_path in collect_files(base_dir, patterns):
            rel_path = file_path.relative_to(base_dir)
            out.write(f"\n\n# ===== FILE: {rel_path} =====\n")
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    out.write(f.read())
            except Exception as e:
                out.write(f"\n# Could not read file {rel_path}: {e}\n")

    print(f"✅ Combined file written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

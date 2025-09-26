#!/usr/bin/env python3
"""
Combine only Django model files into one single text file for ChatGPT context.
"""

import os
from pathlib import Path

OUTPUT_FILE = "all_models_combined.txt"
EXCLUDE_DIRS = {".git", ".venv", "__pycache__", "node_modules"}
IGNORE_FILE = ".gitignore"
TODO_FILE = "chatgpt_todo.txt"


def load_gitignore_patterns(base_dir: Path):
    """Load ignore patterns from .gitignore if available."""
    gitignore_path = base_dir / IGNORE_FILE
    patterns = []
    if gitignore_path.exists():
        with open(gitignore_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.append(line)
    return patterns


def is_ignored(path: Path, patterns: list[str]) -> bool:
    """Check if path matches any gitignore pattern (basic glob)."""
    for pat in patterns:
        if path.match(pat) or str(path).startswith(pat):
            return True
    return False


def should_include_file(file: Path) -> bool:
    """Return True if file should be included (only *.py inside models/)."""
    return (
        "models" in file.parts
        and file.suffix == ".py"
        and file.name != "__init__.py"
    )


def collect_files(base_dir: Path, patterns: list[str]):
    """Yield all relevant model files to include, except chatgpt_todo.txt (added last)."""
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for file in files:
            file_path = Path(root) / file
            if file.lower() == TODO_FILE.lower():
                continue
            if should_include_file(file_path) and not is_ignored(file_path.relative_to(base_dir), patterns):
                yield file_path


def main():
    base_dir = Path(".").resolve()
    patterns = load_gitignore_patterns(base_dir)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        # === WRITE INSTRUCTION BLOCK AT TOP ===
        out.write(
            """
# =============================================================================
CHATGPT_INSTRUCTION:
forget_previous = true
context = this_file
later_files_override = true
todo_mode = if_present
default_reply = "understand all: Awaiting your instructions."
# =============================================================================            
### BEGIN CHATGPT_INSTRUCTION            
# 🚨 INSTRUCTION FOR CHATGPT 🚨
#
# This file is a combined snapshot of only the Django model files.
# It contains:
#   - All Python model files under apps/*/models/
#
# Purpose:
#   - Forget all previously remembered source code in this chat.
#   - Only keep THIS file as the single source of truth.
#   - When the user uploads this file in a new chat, reset context.
#   - Later uploaded individual files override the versions here.
#
# Rules:
#   - Do NOT suggest schema changes blindly.
#   - Always respect definitions and order in this file.
#   - Keep answers focused, avoid code duplication unless asked.
#
# Special:
#   - If a file named `chatgpt_todo.txt` is included at the end,
#     treat it as the active task list and follow it literally.
#   - If no such file exists, you MUST ONLY reply with exactly:
#       "understand all: Awaiting your instructions."
#     Do NOT add examples, do NOT summarize, do NOT guess.
### END CHATGPT_INSTRUCTION
# =============================================================================

"""
        )

        # === MODEL FILES ===
        for file_path in collect_files(base_dir, patterns):
            rel_path = file_path.relative_to(base_dir)
            out.write(f"\n\n# ===== FILE: {rel_path} =====\n")
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    out.write(f.read())
            except Exception as e:
                out.write(f"\n# Could not read file {rel_path}: {e}\n")

        # === APPEND TODO LAST ===
        for todo_candidate in base_dir.rglob("*"):
            if todo_candidate.name.lower() == TODO_FILE.lower():
                rel_path = todo_candidate.relative_to(base_dir)
                out.write(f"\n\n# ===== FILE: {rel_path} =====\n")
                try:
                    with open(todo_candidate, "r", encoding="utf-8") as f:
                        out.write(f.read())
                except Exception as e:
                    out.write(f"\n# Could not read file {rel_path}: {e}\n")
                break

    print(f"✅ Combined file written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

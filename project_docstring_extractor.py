#!/usr/bin/env python3
"""
Project Docstring Extractor:
- Scans all *.py files under INCLUDE_DIRS
- Collects ONLY the very first docstring (before any import/include)
- Skips files without such a docstring
- Writes results into PROJECT_DOCSTRINGS.md
"""

import os
from pathlib import Path

INCLUDE_DIRS = ["apps"]
OUTPUT_DOCSTRINGS = Path("PROJECT_DOCSTRINGS.md")


def extract_first_docstring(file_path: Path) -> str | None:
    """Extract first top-level docstring before any import/include line."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            inside_docstring = False
            quote = None
            buffer = []

            for line in f:
                stripped = line.strip()

                # skip empty lines and comments
                if not inside_docstring and (not stripped or stripped.startswith("#")):
                    continue

                # if import/from before docstring → abort
                if not inside_docstring and (
                    stripped.startswith("import ") or stripped.startswith("from ")
                ):
                    return None

                # start of docstring
                if not inside_docstring and (
                    stripped.startswith('"""') or stripped.startswith("'''")
                ):
                    quote = stripped[:3]
                    content = stripped[3:]
                    # single-line docstring """text"""
                    if content.endswith(quote):
                        return content[:-3].strip()
                    inside_docstring = True
                    if content:
                        buffer.append(content)
                    continue

                # inside docstring
                if inside_docstring:
                    if stripped.endswith(quote):
                        buffer.append(stripped[:-3])
                        return "\n".join(buffer).strip()
                    else:
                        buffer.append(line.rstrip("\n"))

            return None
    except Exception:
        return None


def scan_for_docstrings(base_path: Path):
    results = []
    for root, _, files in os.walk(base_path):
        root_path = Path(root)
        if not any(d in str(root_path) for d in INCLUDE_DIRS):
            continue
        for file in files:
            if file.endswith(".py"):
                file_path = root_path / file
                docstring = extract_first_docstring(file_path)
                if docstring:
                    results.append((file_path.relative_to(base_path), docstring))
    return results


def build_docstrings_file(base_path: Path):
    collected = scan_for_docstrings(base_path)
    lines = ["# Project Docstrings\n"]

    for file_path, docstring in sorted(collected):
        lines.append(f"## File: `{file_path}`")
        lines.append("```")
        lines.append(docstring)
        lines.append("```")
        lines.append("")

    OUTPUT_DOCSTRINGS.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ {OUTPUT_DOCSTRINGS} created with {len(collected)} docstrings.")


if __name__ == "__main__":
    base_path = Path(".").resolve()
    build_docstrings_file(base_path)

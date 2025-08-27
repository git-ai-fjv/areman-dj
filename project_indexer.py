#!/usr/bin/env python3
"""
Enhanced Project Scanner:
- Creates PROJECT_OVERVIEW.md (detailed structure)
- Creates PROJECT_SKELETON.py (skeleton code)
- Creates PROJECT_INDEX.md (flat overview index)
"""

import os
import re
from pathlib import Path

INCLUDE_DIRS = ["apps"]
INCLUDE_EXTENSIONS = [
    ".py", ".dart", ".js", ".ts", ".sh",
    ".yaml", ".yml", ".conf", ".ini",
    ".sql", ".json", ".toml", ".cfg", ".env"
]
OUTPUT_OVERVIEW = Path("PROJECT_OVERVIEW.md")
OUTPUT_SKELETON = Path("PROJECT_SKELETON.py")
OUTPUT_INDEX = Path("PROJECT_INDEX.md")

def is_included_file(file_path: Path) -> bool:
    return file_path.suffix in INCLUDE_EXTENSIONS

def extract_code_structure(file_path: Path) -> list:
    """Extract classes, methods, functions, decorators, Django fields."""
    structure = []
    current_class = None
    class_indent = None

    py_class_regex = re.compile(r'^class\s+(\w+)')
    py_func_regex = re.compile(r'^def\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*([^:]+))?:')
    py_decorator_regex = re.compile(r'^@(\w+)')
    py_field_regex = re.compile(r'(\w+)\s*=\s*models\.(\w+)')

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line_strip = line.strip()

                # Python specifics
                if file_path.suffix == ".py":
                    if py_decorator_regex.match(line_strip):
                        decorator = py_decorator_regex.match(line_strip).group(1)
                        structure.append(f"- Decorator: @{decorator}")

                    class_match = py_class_regex.match(line_strip)
                    func_match = py_func_regex.match(line_strip)
                    field_match = py_field_regex.search(line_strip)

                    if class_match:
                        current_class = class_match.group(1)
                        structure.append(f"- Class: {current_class}")
                        class_indent = len(line) - len(line.lstrip())

                    elif func_match:
                        name = func_match.group(1)
                        params = func_match.group(2).strip()
                        return_type = func_match.group(3).strip() if func_match.group(3) else "None"
                        signature = f"{name}({params}) -> {return_type}"

                        indent = len(line) - len(line.lstrip())
                        if current_class and indent > class_indent:
                            structure.append(f"    - Method: {signature}")
                        else:
                            current_class = None
                            structure.append(f"- Function: {signature}")

                    elif field_match and current_class:
                        fname, ftype = field_match.groups()
                        structure.append(f"    - Field: {fname} ({ftype})")

                # Dart classes/functions
                elif file_path.suffix == ".dart":
                    class_match = re.match(r'^class\s+(\w+)', line_strip)
                    func_match = re.match(r'^(?:\w+\s+)?(\w+)\s*\(([^)]*)\)', line_strip)
                    if class_match:
                        current_class = class_match.group(1)
                        structure.append(f"- Class: {current_class}")
                    elif func_match and not line_strip.startswith("//"):
                        name = func_match.group(1)
                        params = func_match.group(2)
                        if current_class and line.startswith("  "):
                            structure.append(f"    - Method: {name}({params})")
                        else:
                            structure.append(f"- Function: {name}({params})")

    except Exception:
        pass
    return structure

def structure_to_skeleton(structure: list[str]) -> list[str]:
    """Convert structure lines into Python skeleton code."""
    skeleton = []
    for line in structure:
        if line.startswith("- Class: "):
            class_name = line.replace("- Class: ", "").strip()
            skeleton.append(f"class {class_name}:")
            skeleton.append(f"    \"\"\"Skeleton class {class_name}\"\"\"")
            skeleton.append("    pass\n")

        elif line.startswith("- Function: "):
            func = line.replace("- Function: ", "").strip()
            skeleton.append(f"def {func}:")
            skeleton.append(f"    \"\"\"Skeleton function {func}\"\"\"")
            skeleton.append("    pass\n")

        elif line.startswith("    - Method: "):
            method = line.replace("    - Method: ", "").strip()
            skeleton.append(f"    def {method}:")
            skeleton.append(f"        \"\"\"Skeleton method {method}\"\"\"")
            skeleton.append("        pass\n")

    return skeleton

def scan_directory(base_path: Path):
    project_summary = []
    for root, _, files in os.walk(base_path):
        root_path = Path(root)
        if not any(d in str(root_path) for d in INCLUDE_DIRS):
            continue
        for file in files:
            file_path = root_path / file
            if is_included_file(file_path):
                try:
                    line_count = sum(1 for _ in open(file_path, "r", encoding="utf-8", errors="ignore"))
                except Exception:
                    line_count = 0

                if line_count > 1000:
                    structure = ["(skipped details due to size)"]
                else:
                    structure = extract_code_structure(file_path)

                project_summary.append((file_path.relative_to(base_path), line_count, structure))
    return project_summary

def build_overview_and_skeleton(base_path: Path):
    summary = scan_directory(base_path)
    lines = ["# Project Overview\n"]
    skeleton_lines = ["#!/usr/bin/env python3", "# Auto-generated skeleton\n"]
    index_lines = ["# Project Index\n"]

    for file_path, line_count, structure in sorted(summary):
        lines.append(f"## File: `{file_path}` ({line_count} lines)")
        index_lines.append(f"- {file_path} → {len([s for s in structure if s.startswith('- Class:')])} classes, "
                           f"{len([s for s in structure if s.startswith('- Function:') or s.strip().startswith('- Method:')])} functions/methods")

        if structure:
            lines.extend(structure)
            skeleton_lines.append(f"\n# --- {file_path} ---")
            skeleton_lines.extend(structure_to_skeleton(structure))
        else:
            lines.append("- No classes or functions found")
        lines.append("")

    OUTPUT_OVERVIEW.write_text("\n".join(lines), encoding="utf-8")
    OUTPUT_SKELETON.write_text("\n".join(skeleton_lines), encoding="utf-8")
    OUTPUT_INDEX.write_text("\n".join(index_lines), encoding="utf-8")

    print(f"✅ {OUTPUT_OVERVIEW} created with {len(summary)} files.")
    print(f"✅ {OUTPUT_SKELETON} created.")
    print(f"✅ {OUTPUT_INDEX} created.")

if __name__ == "__main__":
    base_path = Path(".").resolve()
    build_overview_and_skeleton(base_path)

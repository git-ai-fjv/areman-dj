#!/usr/bin/env python3
import os
import re
from pathlib import Path

INCLUDE_DIRS = ["apps",]
INCLUDE_EXTENSIONS = [".py", ".dart", ".js", ".ts", ".sh", ".yaml", ".yml", ".conf", ".ini"]
OUTPUT_FILE = Path("PROJECT_OVERVIEW.md")
SKELETON_FILE = Path("PROJECT_SKELETON.py")

def is_included_file(file_path: Path) -> bool:
    return file_path.suffix in INCLUDE_EXTENSIONS

def extract_code_structure(file_path: Path) -> list:
    """Extract classes and methods with parameters and return types."""
    structure = []
    current_class = None
    class_indent = None

    py_class_regex = re.compile(r'^class\s+(\w+)')
    py_func_regex = re.compile(r'^def\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*([^:]+))?:')

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line_strip = line.strip()

                if file_path.suffix == ".py":
                    class_match = py_class_regex.match(line_strip)
                    func_match = py_func_regex.match(line_strip)

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
    """Convert structure lines into a Python skeleton code."""
    skeleton = []
    current_class = None

    for line in structure:
        if line.startswith("- Class: "):
            class_name = line.replace("- Class: ", "").strip()
            skeleton.append(f"class {class_name}:")
            skeleton.append(f"    \"\"\"Skeleton class {class_name}\"\"\"")
            skeleton.append("    pass\n")
            current_class = class_name

        elif line.startswith("- Function: "):
            func = line.replace("- Function: ", "").strip()
            skeleton.append(f"def {func}:")
            skeleton.append(f"    \"\"\"Skeleton function {func}\"\"\"")
            skeleton.append("    pass\n")
            current_class = None

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
                structure = extract_code_structure(file_path)
                project_summary.append((file_path.relative_to(base_path), line_count, structure))
    return project_summary

def build_overview_and_skeleton(base_path: Path):
    summary = scan_directory(base_path)
    lines = ["# Project Overview\n"]
    skeleton_lines = ["#!/usr/bin/env python3", "# Auto-generated skeleton\n"]

    for file_path, line_count, structure in sorted(summary):
        lines.append(f"## File: `{file_path}` ({line_count} lines)")
        if structure:
            lines.extend(structure)
            skeleton_lines.append(f"\n# --- {file_path} ---")
            skeleton_lines.extend(structure_to_skeleton(structure))
        else:
            lines.append("- No classes or functions found")
        lines.append("")  # Blank line between files

    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    SKELETON_FILE.write_text("\n".join(skeleton_lines), encoding="utf-8")

    print(f"✅ PROJECT_OVERVIEW.md created with {len(summary)} files.")
    print(f"✅ PROJECT_SKELETON.py created.")

if __name__ == "__main__":
    base_path = Path(".").resolve()
    build_overview_and_skeleton(base_path)


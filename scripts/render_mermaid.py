#!/usr/bin/env python3
# scripts/render_mermaid.py
# Created according to the user's Copilot Base Instructions.

from __future__ import annotations

import subprocess
from pathlib import Path
import argparse
import sys


def render_mmd_file(mmd_file: Path, out_dir: Path, fmt: str = "svg") -> None:
    """Render one .mmd file to the given format using mermaid-cli (mmdc)."""
    out_file = out_dir / f"{mmd_file.stem}.{fmt}"
    try:
        subprocess.run(
            ["mmdc", "-i", str(mmd_file), "-o", str(out_file)],
            check=True,
        )
        print(f"✅ Rendered {mmd_file} → {out_file}")
    except FileNotFoundError:
        print("❌ Error: 'mmdc' not found. Install with: npm install -g @mermaid-js/mermaid-cli")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to render {mmd_file}: {e}")


def render_all(src_dir: Path, out_dir: Path, fmt: str = "svg") -> None:
    """Render all .mmd files from src_dir into out_dir."""
    out_dir.mkdir(parents=True, exist_ok=True)
    files = list(src_dir.glob("*.mmd"))
    if not files:
        print(f"⚠️  No .mmd files found in {src_dir}")
        return

    for f in files:
        render_mmd_file(f, out_dir, fmt)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Render all Mermaid .mmd files to SVG/PNG/PDF.")
    parser.add_argument(
        "--src", type=str, default="scripts/erd",
        help="Source directory containing .mmd files (default: scripts/erd)"
    )
    parser.add_argument(
        "--out", type=str, default="scripts/erd/out",
        help="Output directory for rendered erd (default: scripts/erd/out)"
    )
    parser.add_argument(
        "--fmt", type=str, choices=["svg", "png", "pdf"], default="svg",
        help="Output format (svg, png, pdf). Default: svg"
    )
    args = parser.parse_args()

    render_all(Path(args.src), Path(args.out), args.fmt)

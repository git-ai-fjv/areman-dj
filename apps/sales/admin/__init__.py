#!/usr/bin/env python3
# Created according to the user's permanent Copilot Base Instructions.
# Auto-import all modules in this package so Django sees each model file.
from __future__ import annotations
from importlib import import_module
from pathlib import Path
import pkgutil

_pkg = __package__
_pkg_path = Path(__file__).parent

for _, module_name, is_pkg in pkgutil.iter_modules([str(_pkg_path)]):
    if not is_pkg and module_name != "__init__":
        import_module(f"{_pkg}.{module_name}")

#!/usr/bin/env python3
# scripts/gen_mermaid_er.py
# Created according to the user's Copilot Base Instructions.

from __future__ import annotations

import argparse
from pathlib import Path
import django
from django.apps import apps
from django.db import models

# --- Django Setup ---
import bootstrap_django  # noqa: F401
django.setup()

RELATION_SYMBOLS = {
    "ForeignKey": "||--o{  (one-to-many)",
    "OneToOneField": "||--|| (one-to-one)",
    "ManyToManyField": "}o--o{ (many-to-many)",
}

EXCLUDE_PREFIXES = (
    "auth_", "django_", "admin_", "contenttypes_", "sessions_",
)


def field_type_name(field: models.Field) -> str:
    """Return simplified field type name."""
    return field.get_internal_type()


def include_model(model: models.Model) -> bool:
    """Filter out Django-internal apps/tables."""
    table = model._meta.db_table or model.__name__
    for prefix in EXCLUDE_PREFIXES:
        if table.startswith(prefix):
            return False
    return True


def generate_mermaid(models_list) -> str:
    """Generate Mermaid ER diagram code for a given list of models."""
    lines: list[str] = ["erDiagram"]

    # --- Legend ---
    lines.append("    %% Relation symbols legend")
    for name, symbol in RELATION_SYMBOLS.items():
        lines.append(f"    %% {symbol}  <= {name}")
    lines.append("")

    # Tables
    for model in models_list:
        if not include_model(model):
            continue

        table = model._meta.db_table or model.__name__
        table = table.replace(".", "_").upper()

        lines.append(f"    {table} {{")
        for field in model._meta.get_fields():
            if isinstance(field, (models.ManyToOneRel, models.ManyToManyRel, models.OneToOneRel)):
                continue
            if isinstance(field, (models.ForeignKey, models.OneToOneField, models.ManyToManyField)):
                continue
            ftype = field_type_name(field)
            lines.append(f"        {ftype} {field.name}")
        lines.append("    }")

    # Relations
    for model in models_list:
        if not include_model(model):
            continue

        source = model._meta.db_table or model.__name__
        source = source.replace(".", "_").upper()

        for field in model._meta.get_fields():
            if isinstance(field, (models.ForeignKey, models.OneToOneField)):
                target_model = field.related_model
                if not include_model(target_model):
                    continue
                target = target_model._meta.db_table.replace(".", "_").upper()
                rel_type = RELATION_SYMBOLS[type(field).__name__].split()[0]
                lines.append(f"    {target} {rel_type} {source} : {field.name}")

            if isinstance(field, models.ManyToManyField):
                target_model = field.related_model
                if not include_model(target_model):
                    continue
                target = target_model._meta.db_table.replace(".", "_").upper()
                rel_type = RELATION_SYMBOLS["ManyToManyField"].split()[0]
                lines.append(f"    {source} {rel_type} {target} : {field.name}")

    return "\n".join(lines)


def write_file(path: Path, code: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(code)
    print(f"✅ Mermaid ERD written to {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Mermaid ER diagrams from Django models.")
    parser.add_argument(
        "--per-app",
        action="store_true",
        help="Generate one ERD per Django app instead of a single big diagram.",
    )
    parser.add_argument(
        "--outdir",
        type=str,
        default="scripts/erd",
        help="Output directory for .mmd files (default: scripts/erd).",
    )
    args = parser.parse_args()

    out_dir = Path(args.outdir)

    if args.per_app:
        for app_config in apps.get_app_configs():
            models_list = [m for m in app_config.get_models() if include_model(m)]
            if not models_list:
                continue
            mermaid_code = generate_mermaid(models_list)
            out_file = out_dir / f"er_{app_config.label}.mmd"
            write_file(out_file, mermaid_code)
    else:
        models_list = [m for m in apps.get_models() if include_model(m)]
        mermaid_code = generate_mermaid(models_list)
        out_file = out_dir / "er_diagram.mmd"
        write_file(out_file, mermaid_code)

# Eine grosse Datei:
# ./scripts/gen_mermaid_er.py
#
# Eine app pro Datei:
# ./scripts/gen_mermaid_er.py --per-app
#
# anderes Ziel:
# ./scripts/gen_mermaid_er.py --per-app --outdir diagrams

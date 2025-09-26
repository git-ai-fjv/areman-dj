#!/usr/bin/env python3

# apps/imports/management/commands/seed_import_defaults.py
"""
Purpose:
    Management command to seed an `ImportGlobalDefaultSet` with related
    `ImportGlobalDefaultLine` entries. Ensures organizations have baseline
    default mappings for import processing.

Context:
    Part of the `apps.imports` app. Used during system setup or onboarding
    to initialize import defaults for a given organization.

Used by:
    - Developers and operators via `python manage.py seed_import_defaults`
    - Import processing logic that relies on a default set of rules

Depends on:
    - apps.core.models.organization.Organization
    - apps.imports.services.import_defaults_ops.seed_initial_defaults
    - Django management command framework

Example:
    # Seed defaults for first organization (today as valid_from)
    python manage.py seed_import_defaults

    # Seed defaults for organization 1, with explicit date
    python manage.py seed_import_defaults --org 1 --valid-from 2025-01-01
"""



from __future__ import annotations

from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.core.models.organization import Organization
from apps.imports.services import import_defaults_ops as ops


class Command(BaseCommand):
    """
    Seed ImportGlobalDefaultSet and ImportGlobalDefaultLine with initial values.
    """

    help = "Create or reuse an ImportGlobalDefaultSet with default lines for an organization."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--org",
            type=int,
            default=None,
            help="Organization ID (defaults to first Organization).",
        )
        parser.add_argument(
            "--valid-from",
            type=str,
            default=None,
            help="Optional: valid-from date (YYYY-MM-DD). Defaults to today.",
        )

    def handle(self, *args, **options) -> None:
        org_id = options["org"]
        valid_from_opt = options["valid_from"]

        # 1. Organization bestimmen
        if org_id:
            try:
                org = Organization.objects.get(pk=org_id)
            except Organization.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Organization with id={org_id} not found."))
                return
        else:
            org = Organization.objects.first()
            if not org:
                self.stdout.write(self.style.ERROR("No Organization found in database."))
                return

        # 2. Datum bestimmen
        if valid_from_opt:
            valid_from = datetime.strptime(valid_from_opt, "%Y-%m-%d").date()
        else:
            valid_from = timezone.now().date()

        # 3. Seed ausführen (idempotent)
        default_set, created = ops.seed_initial_defaults(org, valid_from)

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Created ImportGlobalDefaultSet {default_set.id} "
                    f"with {default_set.global_default_lines.count()} lines "
                    f"(valid_from={valid_from}, org={org.pk})."
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠ Using existing ImportGlobalDefaultSet {default_set.id} "
                    f"with {default_set.global_default_lines.count()} lines "
                    f"(valid_from={valid_from}, org={org.pk})."
                )
            )

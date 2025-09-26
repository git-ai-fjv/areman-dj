# apps/imports/management/commands/seed_import_map_komatsu.py

"""
Purpose:
    Seed an ImportMapSet + ImportMapDetails for supplier Komatsu.
    This defines how raw Komatsu Excel/CSV fields map into the ERP schema.

Context:
    Part of the imports seeding utilities.
    Used to quickly register a supplier-specific mapping that the
    normalize_records command can later apply.

Example:
    python manage.py seed_import_map_komatsu --supplier 70002 --org 1
"""

from __future__ import annotations
from datetime import date

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.imports.models.import_map_set import ImportMapSet
from apps.imports.models.import_map_detail import ImportMapDetail
from apps.imports.models.import_data_type import ImportDataType
from apps.imports.models.import_source_type import ImportSourceType
from apps.partners.models.supplier import Supplier
from apps.core.models.organization import Organization


class Command(BaseCommand):
    help = "Seed ImportMapSet + ImportMapDetails for Komatsu supplier."

    def add_arguments(self, parser):
        parser.add_argument("--supplier", type=int, required=True,
                            help="Supplier code (e.g. 70002 for Komatsu).")
        parser.add_argument("--org", type=int, required=True,
                            help="Organization ID.")

    @transaction.atomic
    def handle(self, *args, **options):
        supplier_code = str(options["supplier"])
        org_id = options["org"]

        try:
            supplier = Supplier.objects.get(supplier_code=supplier_code)
        except Supplier.DoesNotExist:
            raise CommandError(f"Supplier with supplier_code={supplier_code} not found")

        try:
            org = Organization.objects.get(pk=org_id)
        except Organization.DoesNotExist:
            raise CommandError(f"Organization {org_id} not found")

        try:
            source_type = ImportSourceType.objects.get(code="file")
        except ImportSourceType.DoesNotExist:
            raise CommandError("ImportSourceType 'file' not found")

        map_set, created = ImportMapSet.objects.get_or_create(
            organization=org,
            supplier=supplier,
            source_type=source_type,
            valid_from=date.today(),
            defaults={"description": "Komatsu Excel/CSV mapping"},
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"{'Created' if created else 'Reused'} ImportMapSet id={map_set.id}"
            )
        )

        # Helpers
        def dt(code: str) -> ImportDataType:
            return ImportDataType.objects.get(code=code)

        # Mapping rules (Komatsu-specific fields)
        mappings = [
            ("Part Number", "product.productNumber", "str", True, None),
            ("Beschreibung", "product.name", "str", True, None),
            ("Listenpreis", "price.price", "decimal", True, "decimal"),
            ("Returnable Y/N", "variant.is_returnable", "bool", False, "bool"),
            ("Weight in gramms", "variant.weight", "decimal", False, "decimal"),
            ("Customs Commodity Code", "variant.customs_code", "str", False, None),
        ]

        for source, target, dtype, required, transform in mappings:
            detail, _ = ImportMapDetail.objects.update_or_create(
                map_set=map_set,
                source_path=source,
                target_path=target,
                defaults={
                    "target_datatype": dt(dtype),
                    "is_required": required,
                    "transform": transform,
                },
            )
            self.stdout.write(f"  Mapping {source} → {target} ({dtype})")

        self.stdout.write(self.style.SUCCESS("Komatsu mapping seeded successfully."))

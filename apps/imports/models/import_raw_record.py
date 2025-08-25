# apps/imports/models/import_raw_record.py
# Created according to the user's permanent Copilot Base Instructions.
from __future__ import annotations

from django.db import models
from django.utils import timezone


class ImportRawRecord(models.Model):
    """
    Generic raw import storage for supplier/customer integrations.
    Stores unmodified payloads (JSON, XML, CSV rows, etc.) for auditing and reprocessing.
    """

    supplier = models.ForeignKey(
        "partners.Supplier",
        on_delete=models.CASCADE,
        related_name="import_raw_records",
        help_text="Supplier that delivered this raw record.",
    )
    external_id = models.CharField(
        max_length=255,
        help_text="Unique identifier from the external system (if available).",
    )
    payload = models.JSONField(
        help_text="Full raw payload from the external source (JSON or converted dict)."
    )
    fetched_at = models.DateTimeField(
        default=timezone.now,
        help_text="Timestamp when this record was fetched from the external system.",
    )

    class Meta:
        db_table = "partners_import_raw_record"
        app_label = "imports"  # 🔑 wichtig: gehört jetzt zur App `imports`
        indexes = [
            models.Index(fields=["supplier", "external_id"]),
        ]
        unique_together = ("supplier", "external_id")

    def __str__(self) -> str:
        return f"{self.supplier.supplier_code}:{self.external_id}"


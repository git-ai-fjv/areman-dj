# apps/imports/models/import_raw_record.py
# Created according to the user's permanent Copilot Base Instructions.
from __future__ import annotations
from django.db import models
from django.utils import timezone


class ImportRawRecord(models.Model):
    """
    Raw import storage for supplier/customer integrations.
    Stores unmodified payloads (JSON, XML, CSV rows, etc.) for auditing, error handling and reprocessing.
    """

    import_run = models.ForeignKey(
        "imports.ImportRun",
        on_delete=models.CASCADE,
        related_name="raw_records",
        help_text="Import run this record belongs to.",
    )

    line_number = models.IntegerField(
        help_text="Sequential line number within the import run (starting at 1)."
    )

    payload = models.JSONField(
        help_text="Full raw payload from the external source (JSON or converted dict)."
    )

    supplier_product_reference = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        help_text="Supplier's article reference (e.g., supplier SKU or manufacturer number) for fast lookup.",
    )

    is_imported = models.BooleanField(
        default=False,
        help_text="True if this record has been successfully imported into ERP tables.",
    )

    imported_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when this record was imported.",
    )

    is_error = models.BooleanField(
        default=False,
        help_text="True if processing this record failed.",
    )

    error_message = models.TextField(
        null=True,
        blank=True,
        help_text="Detailed error message if processing failed.",
    )

    retry_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times this record has been retried for processing.",
    )

    class Meta:
        verbose_name = "Import Raw Record"
        verbose_name_plural = "Import Raw Records"
        constraints = [
            models.UniqueConstraint(
                fields=["import_run", "line_number"],
                name="uniq_import_run_line",
            )
        ]

    def __str__(self) -> str:
        return (
            f"Run {self.import_run_id}, line {self.line_number}, "
            f"ref={self.supplier_product_reference or 'n/a'}"
        )

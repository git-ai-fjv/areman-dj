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
        return f"Run {self.import_run_id}, line {self.line_number}"


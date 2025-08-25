# apps/imports/models/import_run.py
# Created according to the user's permanent Copilot Base Instructions.
from __future__ import annotations
from django.db import models
from django.utils import timezone


class ImportRun(models.Model):
    """
    Represents a single supplier import execution (the header).
    Tracks metadata and overall status of the import process.
    """

    supplier = models.ForeignKey(
        "partners.Supplier",
        on_delete=models.PROTECT,
        related_name="import_runs",
        help_text="Supplier this import run belongs to."
    )

    source_type = models.ForeignKey(
        "imports.ImportSourceType",
        on_delete=models.PROTECT,
        related_name="import_runs",
        help_text="Type of source for this import (e.g., file, API)."
    )

    source_file = models.CharField(
        max_length=500,
        help_text="Absolute or relative path to the source file that was imported.",
        null=True,
        blank=True,
    )

    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        default="running",
        help_text="running, success, failed"
    )
    total_records = models.IntegerField(
        null=True,
        blank=True,
        help_text="Number of raw records fetched in this run."
    )

    is_processed = models.BooleanField(
        default=False,
        help_text="Marks whether this run has already been processed into ERP tables."
    )

    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when raw records were processed into ERP tables."
    )

    class Meta:
        verbose_name = "Import Run"
        verbose_name_plural = "Import Runs"

    def __str__(self) -> str:
        return f"ImportRun {self.id} — {self.supplier.supplier_code} at {self.started_at:%Y-%m-%d %H:%M}"


# apps/imports/models/import_run.py
"""
Purpose:
    Represents a single supplier import execution (header record).
    Tracks metadata about the run, including timing, status, source, and counts.

Context:
    Belongs to the imports domain. Each ImportRun serves as the parent entity
    for ImportRawRecord entries and error logs. Used to monitor the lifecycle
    of an import job.

Fields:
    - supplier (FK → Supplier): Supplier this run belongs to.
    - source_type (FK → ImportSourceType): Type of source (e.g., file, API, CSV).
    - source_file (CharField, 500, optional): Path or identifier of the imported file.
    - started_at (DateTimeField): Timestamp when the import started.
    - finished_at (DateTimeField, optional): Timestamp when the import finished.
    - status (CharField, 20): Run status ("running", "success", "failed").
    - total_records (IntegerField, optional): Number of raw records fetched.
    - is_processed (BooleanField): Whether the run has been processed into ERP tables.
    - processed_at (DateTimeField, optional): Timestamp when records were processed.

Relations:
    - Supplier → multiple ImportRuns (1:n).
    - ImportRun → multiple ImportRawRecord (1:n).
    - ImportRun → multiple ImportErrorLog (1:n).

Used by:
    - Import pipelines for execution tracking and reporting.
    - Error logging and auditing mechanisms.

Depends on:
    - apps.partners.models.Supplier
    - apps.imports.models.ImportSourceType

Example:
    >>> from apps.imports.models import ImportRun
    >>> run = ImportRun.objects.create(
    ...     supplier=supplier,
    ...     source_type=source_type,
    ...     source_file="/imports/supplier_2025-01.csv"
    ... )
    >>> print(run)
    ImportRun 1 — SUPPLIERX at 2025-01-10 12:00
"""


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


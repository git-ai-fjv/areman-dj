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
    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        default="running",
        help_text="running, success, failed"
    )
    total_records = models.IntegerField(default=0)

    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when raw records were processed into ERP tables."
    )

    class Meta:
        db_table = "partners_import_run"
        app_label = "imports"  # 🔑 wichtig: Modell gehört jetzt zur App `imports`

    def __str__(self) -> str:
        return f"ImportRun {self.id} — {self.supplier.supplier_code} at {self.started_at:%Y-%m-%d %H:%M}"

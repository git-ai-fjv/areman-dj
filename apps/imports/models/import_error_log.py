# apps/imports/models/import_error_log.py
# Created according to the user's permanent Copilot Base Instructions.

from __future__ import annotations

from django.db import models


class ImportErrorLog(models.Model):
    """
    Table for logging errors that occur while mapping ImportRawRecord
    entries into structured ERP tables.
    """

    import_run = models.ForeignKey(
        "imports.ImportRun",
        on_delete=models.CASCADE,
        related_name="error_logs",
    )
    line_number = models.IntegerField(null=True, blank=True)
    error_message = models.TextField()
    payload = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Import Error Log"
        verbose_name_plural = "Import Error Logs"

    def __str__(self) -> str:
        return f"Error in run {self.import_run_id} line {self.line_number}: {self.error_message}"


#
# Beispiel:
#
# from apps.imports.models.import_error_log import ImportErrorLog
# from apps.imports.models.import_run import ImportRun
#
# run = ImportRun.objects.first()
# ImportErrorLog.objects.create(
#     import_run=run,
#     line_number=42,
#     error_message="Invalid price format",
#     payload={"Part Number": "X123", "Listenpreis": "abc"}
# )
#
# -> erzeugt einen neuen Fehler-Logeintrag, der später im Admin sichtbar ist.



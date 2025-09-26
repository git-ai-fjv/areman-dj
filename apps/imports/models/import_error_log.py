# apps/imports/models/import_error_log.py
"""
Purpose:
    Logs errors that occur during the import process while transforming
    raw records into structured ERP tables.

Context:
    Part of the `imports` app. Provides visibility into failures when
    processing ImportRawRecord entries inside an ImportRun.

Fields:
    - import_run (FK → imports.ImportRun): The run during which the error occurred.
    - line_number (IntegerField, nullable): Source line number in the raw file.
    - error_message (TextField): Description of the error encountered.
    - payload (JSONField, nullable): Optional snapshot of the input data.
    - created_at (DateTimeField): Timestamp when the error was logged.

Relations:
    - ImportRun → multiple ImportErrorLogs

Used by:
    - Import framework to persist errors for later inspection.
    - Admin/UI for debugging failed imports.

Depends on:
    - apps.imports.models.ImportRun
    - Django ORM

Example:
    >>> from apps.imports.models import ImportErrorLog, ImportRun
    >>> run = ImportRun.objects.first()
    >>> ImportErrorLog.objects.create(
    ...     import_run=run,
    ...     line_number=42,
    ...     error_message="Invalid price format",
    ...     payload={"sku": "X123", "price": "abc"}
    ... )
    <ImportErrorLog: Error in run 1 line 42: Invalid price format>
"""


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



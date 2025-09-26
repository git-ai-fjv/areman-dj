# apps/imports/models/import_raw_record.py
"""
Purpose:
    Stores raw unmodified data from supplier or customer imports. Acts as the
    first persistence layer for payloads before transformation or validation.

Context:
    Belongs to the imports domain. Each ImportRawRecord links to an ImportRun
    and captures a single line/item from the input (JSON, XML, CSV, etc.).
    Used for auditing, debugging, error handling, and retries.

Fields:
    - import_run (FK → ImportRun): The import run this record belongs to.
    - line_number (IntegerField): Sequential number within the run (starting at 1).
    - payload (JSONField): Full raw payload from the external source.
    - supplier_product_reference (CharField, 255, optional): Supplier’s identifier
      (SKU, part number) for fast lookup.
    - product_is_imported / price_is_imported (BooleanField): Flags whether
      this record was successfully imported into ERP/price tables.
    - product_imported_at / price_imported_at (DateTimeField, optional): Timestamps
      for successful imports.
    - is_product_import_error / is_price_import_error (BooleanField): Flags whether
      import attempts failed.
    - error_message_product_import / error_message_price_import (TextField, optional):
      Detailed error messages for failed imports.
    - retry_count_product_import / retry_count_price_import (PositiveIntegerField):
      Number of retries attempted for this record.

Relations:
    - ImportRun → multiple ImportRawRecord (1:n).

Used by:
    - Import pipelines for auditing, retry handling, and debugging.
    - Error logging/reporting systems.

Depends on:
    - apps.imports.models.ImportRun

Example:
    >>> from apps.imports.models import ImportRawRecord, ImportRun
    >>> run = ImportRun.objects.first()
    >>> rec = ImportRawRecord.objects.create(
    ...     import_run=run,
    ...     line_number=1,
    ...     payload={"Part Number": "X123", "Price": "12.50"},
    ...     supplier_product_reference="X123",
    ... )
    >>> print(rec)
    Run 1, line 1, ref=X123
"""


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

    product_is_imported = models.BooleanField(
        default=False,
        help_text="True if this record has been successfully imported into ERP tables.",
    )

    price_is_imported = models.BooleanField(
        default=False,
        help_text="True if this record has been successfully imported into price tables.",
    )


    product_imported_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when this record was imported.",
    )

    price_imported_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when pricing was imported.",
    )

    is_product_import_error = models.BooleanField(
        default=False,
        help_text="True if processing this record failed.",
    )

    is_price_import_error = models.BooleanField(
        default=False,
        help_text="True if processing this record failed.",
    )


    error_message_product_import = models.TextField(
        null=True,
        blank=True,
        help_text="Detailed error message if processing failed.",
    )

    error_message_price_import = models.TextField(
        null=True,
        blank=True,
        help_text="Detailed error message if processing failed.",
    )


    retry_count_product_import = models.PositiveIntegerField(
        default=0,
        help_text="Number of times this record has been retried for processing.",
    )

    retry_count_price_import = models.PositiveIntegerField(
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
        indexes = [
        #     models.Index(fields=["supplier_product_reference"], name="idx_rawrecord_supplier_ref"),
              models.Index(fields=["product_is_imported"], name="idx_rawrecord_product_imported"),
              models.Index(fields=["price_is_imported"], name="idx_rawrecord_price_imported"),
        #     models.Index(fields=["is_product_import_error"], name="idx_rawrecord_product_error"),
        #     models.Index(fields=["is_price_import_error"], name="idx_rawrecord_price_error"),
        #     models.Index(fields=["product_is_imported", "import_run_id"], name="idx_rawrecord_product_imported_run),"
        #     models.Index(fields=["price_is_imported", "import_run_id"], name="idx_rawrecord_price_imported_run),"
        ]

    def __str__(self) -> str:
        return (
            f"Run {self.import_run_id}, line {self.line_number}, "
            f"ref={self.supplier_product_reference or 'n/a'}"
        )

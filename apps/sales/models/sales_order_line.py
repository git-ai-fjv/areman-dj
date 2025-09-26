# apps/sales/models/sales_order_line.py
"""
Purpose:
    Represents an individual line item in a sales order.
    Each line links to a product variant, with ordered quantity and price.

Context:
    Child of SalesOrder. Used to record which items are sold,
    at which price, and in what quantity. Basis for fulfillment and invoicing.

Fields:
    - organization (FK → Organization): Tenant isolation.
    - sales_order (FK → SalesOrder): Parent sales order reference.
    - row_no (SmallInteger): Unique row number per order.
    - variant (FK → ProductVariant): Ordered product variant.
    - qty (Decimal): Ordered quantity (> 0).
    - price_at_order (Decimal): Net price per unit at time of order.
    - note (TextField): Optional line-level note.
    - is_active (Bool): Logical deletion flag.
    - created_at / updated_at: System timestamps.

Constraints:
    - (organization, sales_order, row_no) unique.
    - qty must be > 0.
    - price_at_order must be ≥ 0.

Example:
    >>> from apps.sales.models import SalesOrderLine
    >>> line = SalesOrderLine.objects.create(
    ...     organization=org,
    ...     sales_order=so,
    ...     row_no=1,
    ...     variant=variant,
    ...     qty=10,
    ...     price_at_order=99.99,
    ... )
    >>> print(line)
    [org=MyOrg] SO=SO-2025-001 #1 -> VAR=SKU123
"""


from __future__ import annotations

from django.db import models
from django.db.models import Q
from django.db.models.functions import Now
from django.core.validators import MinValueValidator


class SalesOrderLine(models.Model):
    #id = models.BigAutoField(primary_key=True)

    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.PROTECT,
        related_name="sales_order_lines",
    )

    sales_order = models.ForeignKey(
        "sales.SalesOrder",
        on_delete=models.PROTECT,
        related_name="sales_order_lines",
    )

    row_no = models.SmallIntegerField()  # unique within (org, sales_order)

    variant = models.ForeignKey(
        "catalog.ProductVariant",
        on_delete=models.PROTECT,
        related_name="sales_order_lines",
    )

    qty = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(0.001)],
    )
    price_at_order = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        validators=[MinValueValidator(0)],
    )
    note = models.TextField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(db_default=Now(), editable=False)
    updated_at = models.DateTimeField(db_default=Now(), editable=False)

    def __str__(self) -> str:
        return f"[org={self.organization}] SO={self.sales_order} #{self.row_no} -> VAR={self.variant}"

    class Meta:
        # db_table = "sales_order_line"
        # indexes = [
        #     models.Index(fields=("organization",), name="idx_sol_org"),
        #     models.Index(fields=("sales_order",), name="idx_sol_so"),
        #     models.Index(fields=("variant",), name="idx_sol_variant"),
        #     models.Index(fields=("is_active",), name="idx_sol_act"),
        # ]
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "sales_order", "row_no"),
                name="uniq_sol_org_so_row",
            ),
            models.CheckConstraint(
                name="ck_sol_qty_pos",
                check=Q(qty__gt=0),
            ),
            models.CheckConstraint(
                name="ck_sol_price_nn",
                check=Q(price_at_order__gte=0),
            ),
        ]



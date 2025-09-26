# apps/procurement/models/purchase_order_line.py
"""
Purpose:
    Represents a line item within a purchase order, detailing the product,
    quantity, and price agreed at the time of order placement.

Context:
    Part of the procurement domain. PurchaseOrderLine items belong to a
    PurchaseOrder and specify the concrete products (via SupplierProduct),
    quantities, and pricing used in supplier transactions.

Fields:
    - organization (FK → core.Organization): Owning organization.
    - purchase_order (FK → procurement.PurchaseOrder): Parent purchase order.
    - row_no (SmallIntegerField): Line number, unique per order and organization.
    - supplier_product (FK → procurement.SupplierProduct): Product reference
      from a supplier catalog.
    - qty (DecimalField): Quantity ordered, must be > 0.
    - price_at_order (DecimalField): Unit price at the time of order, >= 0.
    - note (TextField, optional): Freeform note for this line.
    - is_active (BooleanField): Whether the line is active.
    - created_at / updated_at (DateTimeField): Audit timestamps.

Relations:
    - PurchaseOrder → multiple PurchaseOrderLines
    - SupplierProduct → multiple PurchaseOrderLines
    - Organization → multiple PurchaseOrderLines

Used by:
    - Procurement workflows for order fulfillment and invoicing.
    - Stock management and ERP integrations to update inventory.
    - Reporting on purchase details and supplier performance.

Depends on:
    - apps.core.models.Organization
    - apps.procurement.models.PurchaseOrder
    - apps.procurement.models.SupplierProduct

Example:
    >>> from apps.procurement.models import PurchaseOrderLine
    >>> pol = PurchaseOrderLine.objects.create(
    ...     organization=org,
    ...     purchase_order=po,
    ...     row_no=1,
    ...     supplier_product=sp,
    ...     qty=10,
    ...     price_at_order="99.99",
    ... )
    >>> print(pol)
    [org=1] PO=PO-2025-001 #1 -> SP=SP-123
"""


from __future__ import annotations

from django.db import models
from django.db.models import Q
from django.db.models.functions import Now
from django.core.validators import MinValueValidator


class PurchaseOrderLine(models.Model):
    #id = models.BigAutoField(primary_key=True)

    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.PROTECT,
        related_name="purchase_order_lines",
    )

    purchase_order = models.ForeignKey(
        "procurement.PurchaseOrder",
        on_delete=models.PROTECT,
        related_name="purchase_order_lines",
    )
    row_no = models.SmallIntegerField()  # unique je (org, po)

    supplier_product = models.ForeignKey(
        "procurement.SupplierProduct",
        on_delete=models.PROTECT,
        related_name="purchase_order_lines",
    )

    qty = models.DecimalField(
        max_digits=12, decimal_places=3,
        validators=[MinValueValidator(0.001)]
    )
    price_at_order = models.DecimalField(
        max_digits=12, decimal_places=4,
        validators=[MinValueValidator(0)]
    )
    note = models.TextField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(db_default=Now(), editable=False)
    updated_at = models.DateTimeField(db_default=Now(), editable=False)

    def __str__(self) -> str:
        return f"[org={self.organization}] PO={self.purchase_order} #{self.row_no} -> SP={self.supplier_product}"

    class Meta:
        # db_table = "purchase_order_line"
        # indexes = [
        #     models.Index(fields=("organization",), name="idx_pol_org"),
        #     models.Index(fields=("purchase_order",), name="idx_pol_po"),
        #     models.Index(fields=("supplier_product",), name="idx_pol_sp"),
        #     models.Index(fields=("is_active",), name="idx_pol_act"),
        # ]
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "purchase_order", "row_no"),
                name="uniq_pol_org_po_row",
            ),
            models.CheckConstraint(
                name="ck_pol_qty_pos",
                check=Q(qty__gt=0),
            ),
            models.CheckConstraint(
                name="ck_pol_price_nn",
                check=Q(price_at_order__gte=0),
            ),
        ]


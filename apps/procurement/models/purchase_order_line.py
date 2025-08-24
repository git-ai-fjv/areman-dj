# apps/procurement/models/purchase_order_line.py
# Created according to the user's permanent Copilot Base Instructions.


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


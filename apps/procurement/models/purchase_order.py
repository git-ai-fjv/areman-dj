# apps/procurement/models/purchase_order.py
# Created according to the user's permanent Copilot Base Instructions.

from __future__ import annotations

from django.db import models
from django.db.models import Q
from django.db.models.functions import Now


class PurchaseOrder(models.Model):
    #id = models.BigAutoField(primary_key=True)

    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.PROTECT,
        related_name="purchase_orders",
    )

    supplier = models.ForeignKey(
        "partners.Supplier",
        on_delete=models.PROTECT,
        related_name="purchase_orders",
    )

    order_number = models.CharField(max_length=30)  # unique je Org (s.u.)
    status = models.CharField(max_length=20, default="draft")  # draft|approved|ordered|received|cancelled

    currency = models.ForeignKey(
        "core.Currency",
        on_delete=models.PROTECT,
        related_name="purchase_orders",
    )

    expected_date = models.DateField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(db_default=Now(), editable=False)
    updated_at = models.DateTimeField(db_default=Now(), editable=False)

    def __str__(self) -> str:
        return f"[org={self.organization_}] PO {self.order_number} ({self.status})"

    class Meta:
        # db_table = "purchase_order"
        # indexes = [
        #     models.Index(fields=("organization",), name="idx_po_org"),
        #     models.Index(fields=("supplier",),    name="idx_po_supplier"),
        #     models.Index(fields=("status",),      name="idx_po_status"),
        #     models.Index(fields=("expected_date",), name="idx_po_expected"),
        # ]
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "order_number"),
                name="uniq_po_org_number",
            ),
            models.CheckConstraint(
                name="ck_po_status",
                check=Q(status__in=["draft","approved","ordered","received","cancelled"]),
            ),
            models.UniqueConstraint(fields=("organization", "id"), name="uniq_po_org_id"),
        ]

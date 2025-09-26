# apps/procurement/models/purchase_order.py
"""
Purpose:
    Represents a purchase order created by an organization to procure goods
    from a supplier. Captures order number, status, currency, and delivery info.

Context:
    Part of the procurement domain. Purchase orders are used to formalize
    and track purchasing activities, serving as the header document for
    ordered items.

Fields:
    - organization (FK → core.Organization): Owning organization.
    - supplier (FK → partners.Supplier): Supplier to whom the order is placed.
    - order_number (CharField, max 30): Unique identifier per organization.
    - status (CharField, max 20): Workflow state ("draft", "approved", "ordered",
      "received", "cancelled").
    - currency (FK → core.Currency): Currency in which the order is placed.
    - expected_date (DateField, optional): Expected delivery date.
    - notes (TextField, optional): Freeform remarks.
    - is_active (BooleanField): Whether the order is currently active.
    - created_at / updated_at (DateTimeField): Audit timestamps.

Relations:
    - Organization → multiple PurchaseOrders
    - Supplier → multiple PurchaseOrders
    - Currency → multiple PurchaseOrders
    - To be extended by PurchaseOrderLine for itemized order positions.

Used by:
    - Procurement workflows to manage supplier orders.
    - ERP processes for stock, invoicing, and financial reconciliation.
    - Reporting to track supplier performance and order statuses.

Depends on:
    - apps.core.models.Organization
    - apps.core.models.Currency
    - apps.partners.models.Supplier

Example:
    >>> from apps.procurement.models import PurchaseOrder
    >>> po = PurchaseOrder.objects.create(
    ...     organization=org,
    ...     supplier=sup,
    ...     order_number="PO-2025-001",
    ...     status="draft",
    ...     currency=eur,
    ... )
    >>> print(po)
    [org=1] PO PO-2025-001 (draft)
"""


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

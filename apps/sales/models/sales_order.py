# apps/sales/models/sales_order.py
"""
Purpose:
    Represents the header of a sales order, scoped by organization.
    Tracks business partner, currency, status, and important dates.

Context:
    Part of the sales domain. This table is the parent for sales order lines
    and drives fulfillment, invoicing, and reporting.

Fields:
    - organization (FK → Organization): Tenant isolation.
    - customer (FK → Customer): Buyer reference.
    - order_number (CharField): Unique per organization.
    - status (CharField): Lifecycle state (draft|confirmed|shipped|invoiced|cancelled).
    - currency (FK → Currency): Transaction currency.
    - expected_date (DateField): Optional promised delivery date.
    - notes (TextField): Optional free-text notes.
    - is_active (Bool): Logical deletion flag.
    - created_at / updated_at: System timestamps.

Relations:
    - SalesOrder → multiple SalesOrderLine (items).
    - Linked to invoicing, shipping, and pricing modules.

Constraints:
    - (organization, order_number) unique.
    - (organization, id) unique for safety.
    - Status restricted by check constraint.

Example:
    >>> from apps.sales.models import SalesOrder
    >>> so = SalesOrder.objects.create(
    ...     organization=org,
    ...     customer=cust,
    ...     order_number="SO-2025-001",
    ...     currency=eur,
    ... )
    >>> print(so)
    [org=MyOrg] SO SO-2025-001 (draft)
"""


from __future__ import annotations

from django.db import models
from django.db.models import Q
from django.db.models.functions import Now


class SalesOrder(models.Model):
    """Sales order header, scoped by organization."""

    #id = models.BigAutoField(primary_key=True)

    # Tenant
    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.PROTECT,
        related_name="sales_orders",
    )

    # Business relations
    customer = models.ForeignKey(
        "partners.Customer",
        on_delete=models.PROTECT,
        related_name="sales_orders",
    )

    order_number = models.CharField(max_length=30)  # unique per org

    status = models.CharField(
        max_length=20,
        default="draft",  # draft|confirmed|shipped|invoiced|cancelled
    )

    currency = models.ForeignKey(
        "core.Currency",
        on_delete=models.PROTECT,
        related_name="sales_orders",
    )

    expected_date = models.DateField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    # DB-managed timestamps
    created_at = models.DateTimeField(db_default=Now(), editable=False)
    updated_at = models.DateTimeField(db_default=Now(), editable=False)

    def __str__(self) -> str:
        return f"[org={self.organization}] SO {self.order_number} ({self.status})"

    class Meta:
        # db_table = "sales_order"
        # indexes = [
        #     models.Index(fields=("organization",), name="idx_so_org"),
        #     models.Index(fields=("customer",),    name="idx_so_customer"),
        #     models.Index(fields=("status",),      name="idx_so_status"),
        #     models.Index(fields=("expected_date",), name="idx_so_expected"),
        # ]
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "order_number"),
                name="uniq_so_org_number",
            ),
            models.UniqueConstraint(
                fields=("organization", "id"),
                name="uniq_so_org_id",
            ),
            models.CheckConstraint(
                name="ck_so_status",
                check=Q(status__in=["draft", "confirmed", "shipped", "invoiced", "cancelled"]),
            ),
        ]


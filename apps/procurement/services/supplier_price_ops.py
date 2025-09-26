# apps/procurement/services/supplier_price_ops.py
"""
Purpose:
    Provides safe operations for inserting or updating supplier prices.
    Ensures that duplicate entries are avoided and price history is maintained
    by deactivating old records when values change.

Context:
    Part of the `apps.procurement` app. Encapsulates business logic for
    supplier price management, keeping importers and synchronization jobs clean.

Used by:
    - Importers that load supplier price data (CSV, API, Excel)
    - Procurement workflows updating tiered pricing
    - Services that manage SupplierProduct cost data

Depends on:
    - apps.procurement.models.SupplierPrice
    - apps.procurement.models.SupplierQuantityPrice
    - django.utils.timezone for timestamp handling
    - Python's decimal for monetary precision

Example:
    from decimal import Decimal
    from apps.procurement.services.supplier_price_ops import SupplierPriceOps

    supplier_product = SupplierProduct.objects.get(id=1)
    new_price = SupplierPriceOps.upsert_price(
        supplier_product=supplier_product,
        currency="EUR",
        unit_price=Decimal("9.99"),
        quantity_prices=[(Decimal("10"), Decimal("9.50"))],
        valid_from=timezone.now().date(),
    )
    print(new_price.id, new_price.unit_price)
"""


from __future__ import annotations

import decimal
from django.utils import timezone
from apps.procurement.models.supplier_price import SupplierPrice
from apps.procurement.models.supplier_quantity_price import SupplierQuantityPrice



class SupplierPriceOps:
    """
    Operational helper for importing supplier prices safely.
    Prevents duplicate entries by comparing against the last active record.
    """

    @staticmethod
    def upsert_price(
        supplier_product,
        currency: str,
        unit_price: decimal.Decimal | None,
        quantity_prices: list[tuple[decimal.Decimal, decimal.Decimal]] | None = None,
        valid_from=None,
        valid_to=None,
    ) -> SupplierPrice:
        """
        Insert or update supplier price info.
        If price unchanged → update `updated_at`.
        If changed → create new entry and deactivate old one.

        Args:
            supplier_product: SupplierProduct instance
            currency: ISO 4217 code
            unit_price: Single base price (nullable if quantity_prices used)
            quantity_prices: List of tuples (min_qty, price) if tiered pricing
            valid_from: Optional start date
            valid_to: Optional end date
        """

        last_price = (
            SupplierPrice.objects.filter(
                supplier_product=supplier_product,
                currency=currency,
                is_active=True,
            )
            .order_by("-valid_from", "-created_at")
            .first()
        )

        # Check if identical
        if last_price:
            if (
                last_price.unit_price == unit_price
                and last_price.valid_from == valid_from
                and last_price.valid_to == valid_to
                and SupplierPriceOps._quantity_prices_equal(
                    last_price, quantity_prices
                )
            ):
                # Just touch updated_at
                last_price.updated_at = timezone.now()
                last_price.save(update_fields=["updated_at"])
                return last_price

            # Deactivate old one
            last_price.is_active = False
            last_price.save(update_fields=["is_active"])

        # Create new SupplierPrice
        new_price = SupplierPrice.objects.create(
            supplier_product=supplier_product,
            currency=currency,
            unit_price=unit_price,
            valid_from=valid_from,
            valid_to=valid_to,
            is_active=True,
        )

        # Create quantity tiers if given
        if quantity_prices:
            SupplierQuantityPrice.objects.bulk_create(
                [
                    SupplierQuantityPrice(
                        supplier_price=new_price,
                        min_quantity=min_qty,
                        unit_price=price,
                    )
                    for (min_qty, price) in quantity_prices
                ]
            )

        return new_price

    @staticmethod
    def _quantity_prices_equal(
        supplier_price: SupplierPrice, new_qps: list[tuple[decimal.Decimal, decimal.Decimal]] | None
    ) -> bool:
        """
        Compare existing quantity prices with new incoming ones.
        """
        old_qps = list(
            supplier_price.quantity_prices.order_by("min_quantity").values_list(
                "min_quantity", "unit_price"
            )
        )
        new_qps_sorted = sorted(new_qps or [], key=lambda x: x[0])
        return old_qps == new_qps_sorted

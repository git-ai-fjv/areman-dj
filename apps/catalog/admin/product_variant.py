# apps/catalog/admin/product_variant.py
#!/usr/bin/env python3
# Created according to the user's permanent Copilot Base Instructions.
from __future__ import annotations

from django.contrib import admin

from ..models.product_variant import ProductVariant


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    """Admin for catalog.ProductVariant."""

    # Keep rows clickable (standing rule). You can adjust columns later.
    list_display = (
        "id",
        "organization",
        "product",
        "sku",
        "barcode",
        "packing",
        "origin",
        "state",
        "customs_code",
        "weight",
        "is_active",
        "created_at",
        "updated_at",
    )
    list_display_links = ("id", "sku")

    # Useful filters & search.
    list_filter = ("is_active", "organization", "product", "origin", "state", "packing")
    search_fields = ("sku", "barcode")

    # Stable ordering, pagination, and date drilldown.
    ordering = ("organization", "product", "sku")
    list_per_page = 50
    date_hierarchy = "created_at"

    # Performance for large FKs; DB-managed fields are read-only.
    raw_id_fields = ("organization", "product")
    readonly_fields = ("id", "created_at", "updated_at")


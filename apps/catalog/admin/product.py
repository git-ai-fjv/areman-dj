# apps/catalog/admin/product.py
#!/usr/bin/env python3
# Created according to the user's permanent Copilot Base Instructions.
from __future__ import annotations

from django.contrib import admin

from ..models.product import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin for catalog.Product."""

    # Show key fields; make rows clickable (standing rule).
    list_display = (
        "id",
        "organization",
        "manufacturer",
        "name",
        "slug",
        "manufacturer_part_number",
        "product_group",
        "is_active",
        "created_at",
        "updated_at",
    )
    list_display_links = ("id", "name")

    # Fast filtering & search.
    list_filter = ("is_active", "organization", "manufacturer", "product_group")
    search_fields = (
        "name",
        "slug",
        "manufacturer_part_number",
        "manufacturer_part_number_norm",
    )

    # Stable ordering, pagination, and date drilldown.
    ordering = ("organization", "name")
    list_per_page = 50
    date_hierarchy = "created_at"

    # Performance for large FKs; read-only computed/default fields.
    raw_id_fields = ("organization", "manufacturer", "product_group")
    readonly_fields = ("id", "manufacturer_part_number_norm", "created_at", "updated_at")

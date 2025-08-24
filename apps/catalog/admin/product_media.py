# apps/catalog/admin/product_media.py
#!/usr/bin/env python3
# Created according to the user's permanent Copilot Base Instructions.
from __future__ import annotations

from django.contrib import admin

from ..models.product_media import ProductMedia


@admin.register(ProductMedia)
class ProductMediaAdmin(admin.ModelAdmin):
    """Admin for catalog.ProductMedia."""

    # Show key fields; keep rows clickable (standing rule).
    list_display = (
        "id",
        "organization",
        "product",
        "variant",
        "role",
        "sort_order",
        "is_active",
        "mime",
        "width_px",
        "height_px",
        "file_size",
        "created_at",
        "updated_at",
    )
    list_display_links = ("id",)

    # Useful filters & search.
    list_filter = ("is_active", "role", "organization")
    search_fields = ("media_url", "alt_text", "mime")

    # Stable ordering, pagination, and date drilldown.
    ordering = ("organization", "product", "variant", "role", "sort_order", "id")
    list_per_page = 50
    date_hierarchy = "created_at"

    # Performance for large FKs; mark readonly DB-managed fields.
    raw_id_fields = ("organization", "product", "variant")
    readonly_fields = ("id", "created_at", "updated_at")


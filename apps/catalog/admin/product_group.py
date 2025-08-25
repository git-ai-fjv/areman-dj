# apps/catalog/admin/product_group.py
#!/usr/bin/env python3
# Created according to the user's permanent Copilot Base Instructions.
from __future__ import annotations

from django.contrib import admin

from ..models.product_group import ProductGroup


@admin.register(ProductGroup)
class ProductGroupAdmin(admin.ModelAdmin):
    """Admin for catalog.ProductGroup."""

    # Keep rows clickable (standing rule). You can adjust the columns later.
    list_display = ("id", "organization", "product_group_code", "product_group_description")
    list_display_links = ("id", "product_group_code")

    # Useful search/filter + stable ordering.
    search_fields = ("product_group_code", "product_group_description")
    list_filter = ("organization",)
    ordering = ("organization", "product_group_code")

    # Performance
    raw_id_fields = ("organization",)
    list_per_page = 50

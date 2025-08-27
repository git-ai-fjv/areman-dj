# apps/imports/admin/import_map_set.py
# Created according to the user's permanent Copilot Base Instructions.

from __future__ import annotations
from django.contrib import admin
from apps.imports.models.import_map_set import ImportMapSet


@admin.register(ImportMapSet)
class ImportMapSetAdmin(admin.ModelAdmin):
    list_display = ("organization", "supplier", "source_type", "description", "valid_from")
    search_fields = ("description", "supplier__supplier_code", "source_type__code")
    ordering = ("supplier", "valid_from")
    list_filter = ("source_type", "valid_from")
    list_display_links = ("supplier", "source_type", "description")


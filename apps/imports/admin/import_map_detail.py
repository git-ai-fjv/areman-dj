# apps/imports/admin/import_map_detail.py
# Created according to the user's permanent Copilot Base Instructions.

from __future__ import annotations
from django.contrib import admin
from apps.imports.models.import_map_detail import ImportMapDetail


@admin.register(ImportMapDetail)
class ImportMapDetailAdmin(admin.ModelAdmin):
    list_display = ("map_set", "source_path", "target_path", "target_datatype", "is_required")
    search_fields = ("source_path", "target_path", "map_set__description")
    list_filter = ("target_datatype", "is_required")
    ordering = ("map_set", "source_path")
    list_display_links = ("source_path", "target_path")



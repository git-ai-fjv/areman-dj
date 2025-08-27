# apps/imports/admin/import_global_default_line.py
# Created according to the user's permanent Copilot Base Instructions.

from __future__ import annotations
from django.contrib import admin
from apps.imports.models.import_global_default_line import ImportGlobalDefaultLine



@admin.register(ImportGlobalDefaultLine)
class ImportGlobalDefaultLineAdmin(admin.ModelAdmin):
    list_display = (
        "set",
        "target_path",
        "default_value",
        "target_datatype",
        "transform",
        "is_required",
    )
    search_fields = ("target_path", "default_value")
    list_filter = ("is_required", "transform", "target_datatype")
    ordering = ("set", "target_path")
    list_display_links = ("target_path",)

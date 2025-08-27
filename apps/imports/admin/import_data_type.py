# apps/imports/admin/import_data_type.py
# Created according to the user's permanent Copilot Base Instructions.

from __future__ import annotations
from django.contrib import admin
from apps.imports.models.import_data_type import ImportDataType


@admin.register(ImportDataType)
class ImportDataTypeAdmin(admin.ModelAdmin):
    list_display = ("code", "description", "python_type")
    search_fields = ("code", "description", "python_type")
    ordering = ("code",)
    list_display_links = ("code", "description")

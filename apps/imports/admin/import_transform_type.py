# apps/imports/admin/import_transform_type.py

from __future__ import annotations
from django.contrib import admin
from apps.imports.models.import_transform_type import ImportTransformType


@admin.register(ImportTransformType)
class ImportTransformTypeAdmin(admin.ModelAdmin):
    list_display = ("code", "description")
    search_fields = ("code", "description")
    ordering = ("code",)
    list_display_links = ("code",)



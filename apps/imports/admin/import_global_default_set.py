# apps/imports/admin/import_global_default_set.py
# Created according to the user's permanent Copilot Base Instructions.

from __future__ import annotations
from django.contrib import admin
from apps.imports.models.import_global_default_set import ImportGlobalDefaultSet


@admin.register(ImportGlobalDefaultSet)
class ImportGlobalDefaultSetAdmin(admin.ModelAdmin):
    list_display = ("organization", "description", "valid_from", "created_at")
    search_fields = ("description", "organization__name")
    list_filter = ("valid_from", "organization")
    ordering = ("organization", "valid_from")
    list_display_links = ("description", "organization")


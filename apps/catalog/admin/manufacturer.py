# apps/catalog/admin/manufacturer.py
# Created according to the user's Copilot Base Instructions.
from __future__ import annotations

from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered
from apps.catalog.models.manufacturer import Manufacturer


class ManufacturerAdmin(admin.ModelAdmin):
    """Admin for Manufacturer."""
    list_display = ("manufacturer_code", "manufacturer_description")
    list_display_links = ("manufacturer_code", "manufacturer_description")
    search_fields = ("manufacturer_description",)  # code ist int -> nicht in search_fields
    ordering = ("manufacturer_code",)
    list_per_page = 50


# Idempotent registration to avoid AlreadyRegistered on double imports/autoreload
try:
    admin.site.register(Manufacturer, ManufacturerAdmin)
except AlreadyRegistered:
    pass


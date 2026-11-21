"""Django admin for harvested AED sources."""

from django.contrib import admin

from apps.aed.models import SourceDataset, SourceResource


class SourceResourceInline(admin.TabularInline):
    model = SourceResource
    extra = 0
    fields = ("external_id", "title", "format", "fetch_status", "size", "selected", "url")
    readonly_fields = fields
    can_delete = False
    show_change_link = True


@admin.register(SourceDataset)
class SourceDatasetAdmin(admin.ModelAdmin):
    list_display = ("title", "kind", "publisher", "license_name", "source_modified", "harvested_at")
    list_filter = ("kind",)
    search_fields = ("title", "publisher", "external_id")
    inlines = [SourceResourceInline]


@admin.register(SourceResource)
class SourceResourceAdmin(admin.ModelAdmin):
    list_display = ("__str__", "format", "fetch_status", "size", "selected", "fetched_at")
    list_filter = ("fetch_status", "format", "selected", "dataset__kind")
    search_fields = ("title", "url", "dataset__title")
    readonly_fields = ("size", "content_type", "fetched_at", "fetch_status", "fetch_error")

"""Django admin for harvested AED sources."""

from django.contrib import admin

from apps.aed.models import AED, SourceDataset, SourceRecord, SourceResource


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


@admin.register(AED)
class AEDAdmin(admin.ModelAdmin):
    list_display = ("id_aed", "name", "city", "sources_count", "lat", "lon")
    list_filter = ("sources_count",)
    search_fields = ("id_aed", "data__nazwa", "data__miejscowosc")
    readonly_fields = ("id_aed", "lat", "lon", "data", "sources_count", "updated_at")

    @admin.display(description="nazwa")
    def name(self, obj):
        return obj.data.get("nazwa", "")

    @admin.display(description="miejscowość")
    def city(self, obj):
        return obj.data.get("miejscowosc", "")


@admin.register(SourceRecord)
class SourceRecordAdmin(admin.ModelAdmin):
    list_display = ("__str__", "valid", "lat", "lon", "aed")
    list_filter = ("valid", "resource__dataset__kind")
    search_fields = ("source_row_id", "data__nazwa")
    raw_id_fields = ("resource", "aed")
    readonly_fields = ("raw", "data", "quality_flags")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("resource__dataset").defer(
            "resource__raw"
        )

from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html

from mcod.aed.models import (
    AedDevice,
    AedImportRun,
    AedSourceRecord,
    DatasetStandard,
    DataStandard,
    ResourceStandardValidation,
)


def queue_aggregation(request):
    from mcod.aed.tasks import aggregate_task

    who = getattr(request.user, "email", "admin")
    aggregate_task.apply_async(kwargs={"triggered_by": "admin: {}".format(who)})
    messages.success(request, "Agregacja AED została uruchomiona w tle – odśwież listę agregacji za chwilę "
                              "(zwykle ok. 30 s).")


@admin.register(DataStandard)
class DataStandardAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "version", "target_dataset", "max_invalid_ratio", "is_active", "datasets_count",
                    "aggregate_button")
    actions = ["run_aggregation"]
    readonly_fields = ("json_schema", "created", "modified")
    fields = (
        "name",
        "code",
        "version",
        "description",
        "target_dataset",
        "max_invalid_ratio",
        "is_active",
        "json_schema",
        "created",
        "modified",
    )
    raw_id_fields = ("target_dataset",)

    def datasets_count(self, obj):
        return obj.dataset_links.count()

    datasets_count.short_description = "zbiory w standardzie"

    def aggregate_button(self, obj):
        url = reverse("admin:aed_datastandard_aggregate", args=[obj.pk])
        return format_html('<a class="btn btn-primary btn-small" href="{}">Uruchom agregację</a>', url)

    aggregate_button.short_description = "agregacja"

    def run_aggregation(self, request, queryset):
        queue_aggregation(request)

    run_aggregation.short_description = "Uruchom agregację do zbioru zbiorczego"

    def get_urls(self):
        return [path("<int:pk>/aggregate/", self.admin_site.admin_view(self.aggregate_view),
                     name="aed_datastandard_aggregate")] + super().get_urls()

    def aggregate_view(self, request, pk):
        queue_aggregation(request)
        return HttpResponseRedirect(reverse("admin:aed_aedimportrun_changelist"))


@admin.register(DatasetStandard)
class DatasetStandardAdmin(admin.ModelAdmin):
    list_display = ("dataset", "standard", "modified")
    list_filter = ("standard",)
    raw_id_fields = ("dataset",)
    search_fields = ("dataset__title",)


@admin.register(ResourceStandardValidation)
class ResourceStandardValidationAdmin(admin.ModelAdmin):
    list_display = ("resource", "standard", "status", "blocking", "rows_total", "rows_invalid", "validated_at")
    list_filter = ("standard", "status", "blocking")
    raw_id_fields = ("resource",)
    readonly_fields = [f.name for f in ResourceStandardValidation._meta.fields]


@admin.register(AedImportRun)
class AedImportRunAdmin(admin.ModelAdmin):
    list_display = ("started_at", "status", "triggered_by", "sources_count", "records_count", "devices_count",
                    "finished_at", "national_link")
    readonly_fields = ("standard", "started_at", "finished_at", "status", "triggered_by", "sources_count",
                       "records_count", "devices_count", "report")

    def national_link(self, obj):
        national = (obj.report or {}).get("national_dataset")
        if not national:
            return "-"
        return format_html('<a href="{}" target="_blank" rel="noopener">{}</a>', national["url"], national["title"])

    national_link.short_description = "zbiór zbiorczy"

    def has_add_permission(self, request):
        return False


@admin.register(AedDevice)
class AedDeviceAdmin(admin.ModelAdmin):
    list_display = ("id_aed", "name", "town", "sources_count", "lat", "lon")
    list_filter = ("sources_count",)
    search_fields = ("id_aed", "data__nazwa", "data__miejscowosc")
    readonly_fields = ("standard", "id_aed", "lat", "lon", "sources_count", "sources", "data")

    def name(self, obj):
        return obj.data.get("nazwa")

    def town(self, obj):
        return obj.data.get("miejscowosc")

    def has_add_permission(self, request):
        return False


@admin.register(AedSourceRecord)
class AedSourceRecordAdmin(admin.ModelAdmin):
    list_display = ("resource", "row_id", "name", "valid", "device")
    list_filter = ("valid",)
    raw_id_fields = ("resource", "device")
    search_fields = ("row_id", "data__nazwa")
    readonly_fields = ("resource", "dataset_id", "row_id", "data", "lat", "lon", "valid", "quality_flags", "device")

    def name(self, obj):
        return obj.data.get("nazwa")

    def has_add_permission(self, request):
        return False

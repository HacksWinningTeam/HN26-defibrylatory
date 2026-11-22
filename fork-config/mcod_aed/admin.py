from django.contrib import admin

from mcod.aed.models import DatasetStandard, DataStandard, ResourceStandardValidation


@admin.register(DataStandard)
class DataStandardAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "version", "target_dataset", "max_invalid_ratio", "is_active", "datasets_count")
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

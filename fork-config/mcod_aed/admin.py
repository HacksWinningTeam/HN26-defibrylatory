from django import forms
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html, format_html_join

from mcod.aed.models import (
    AedDevice,
    AedImportRun,
    AedSourceRecord,
    DatasetStandard,
    DataStandard,
    ResourceStandardValidation,
)


def queue_aggregation(request, standard):
    """Queue "Agregacja" for exactly this standard (never another one)."""
    from mcod.aed.aggregate import supports_aggregation
    from mcod.aed.tasks import aggregate_task

    if not supports_aggregation(standard):
        messages.warning(request, "Agregacja dla standardu „{}” nie jest jeszcze dostępna (silnik ogólny – zadanie "
                                  "T18). Nic nie zostało uruchomione.".format(standard.name))
        return False
    who = getattr(request.user, "email", "admin")
    aggregate_task.apply_async(kwargs={"triggered_by": "admin: {}".format(who), "standard_code": standard.code})
    messages.success(request, "Agregacja „{}” została uruchomiona w tle – odśwież listę agregacji za chwilę "
                              "(zwykle ok. 30 s).".format(standard.name))
    return True


class DataStandardForm(forms.ModelForm):
    class Meta:
        model = DataStandard
        fields = "__all__"

    def clean(self):
        data = super().clean()
        if self.instance.code == "aed-pl" or data.get("code") == "aed-pl":
            return data  # defined in code (schema.py); fields are a read-only mirror
        from mcod.aed.spec import StandardDefinitionError, StandardSpec

        try:
            spec = StandardSpec(data.get("code") or "", data.get("name") or "", data.get("version") or "1.0.0",
                                data.get("description") or "", data.get("fields") or [], data.get("merge"),
                                data.get("discovery"), data.get("publish"))
        except StandardDefinitionError as exc:
            raise forms.ValidationError(str(exc))
        self.cleaned_data["json_schema"] = spec.json_schema()
        return data


@admin.register(DataStandard)
class DataStandardAdmin(admin.ModelAdmin):
    form = DataStandardForm
    list_display = ("name", "code", "version", "fields_count", "merge_rule", "target_dataset", "max_invalid_ratio",
                    "is_active", "datasets_count", "aggregate_button")
    actions = ["run_aggregation"]

    def get_readonly_fields(self, request, obj=None):
        base = ["fields_table", "json_schema", "created", "modified"]
        if obj is not None and obj.code == "aed-pl":
            base += ["code", "fields", "merge", "discovery", "publish"]
        return base

    def get_fields(self, request, obj=None):
        return ["name", "code", "version", "description", "fields_table", "target_dataset", "max_invalid_ratio",
                "is_active", "merge", "discovery", "publish", "fields", "json_schema", "created", "modified"]

    raw_id_fields = ("target_dataset",)

    def save_model(self, request, obj, form, change):
        if "json_schema" in form.cleaned_data and obj.code != "aed-pl":
            obj.json_schema = form.cleaned_data["json_schema"]
        super().save_model(request, obj, form, change)

    def fields_count(self, obj):
        return len(obj.fields or [])

    fields_count.short_description = "pola"

    def merge_rule(self, obj):
        merge = obj.merge or {}
        if merge.get("strategy") == "key":
            return "klucz: " + " | ".join("+".join(k) for k in merge.get("keys", []))
        if merge.get("strategy") == "geo":
            return "odległość ≤ {} m".format(merge.get("distance_m", 25))
        return merge.get("strategy", "-")

    merge_rule.short_description = "scalanie"

    def fields_table(self, obj):
        if obj is None or not obj.fields:
            return "-"
        rows = format_html_join(
            "",
            "<tr><td><code>{}</code></td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>",
            (
                (f["name"], f.get("label", ""), f.get("type", ""), f.get("obligation", ""),
                 ", ".join(v["value"] for v in f.get("allowed_values", [])) or f.get("pattern") or "",
                 ", ".join(f.get("synonyms", [])))
                for f in obj.fields
            ),
        )
        return format_html(
            '<table class="table table-condensed"><thead><tr><th>pole</th><th>nazwa</th><th>typ</th>'
            "<th>wymagalność</th><th>dozwolone / wzorzec</th><th>inne akceptowane nazwy kolumn</th></tr></thead>"
            "<tbody>{}</tbody></table>", rows)

    fields_table.short_description = "pola standardu"

    def datasets_count(self, obj):
        return obj.dataset_links.count()

    datasets_count.short_description = "zbiory w standardzie"

    def aggregate_button(self, obj):
        url = reverse("admin:aed_datastandard_aggregate", args=[obj.pk])
        return format_html('<a class="btn btn-primary btn-small" href="{}">Uruchom agregację</a>', url)

    aggregate_button.short_description = "agregacja"

    def run_aggregation(self, request, queryset):
        for standard in queryset:
            queue_aggregation(request, standard)

    run_aggregation.short_description = "Uruchom agregację do zbioru zbiorczego"

    def get_urls(self):
        return [path("<int:pk>/aggregate/", self.admin_site.admin_view(self.aggregate_view),
                     name="aed_datastandard_aggregate")] + super().get_urls()

    def aggregate_view(self, request, pk):
        standard = DataStandard.objects.filter(pk=pk).first()
        if standard is None:
            messages.error(request, "Nie ma takiego standardu.")
            return HttpResponseRedirect(reverse("admin:aed_datastandard_changelist"))
        if queue_aggregation(request, standard):
            return HttpResponseRedirect(reverse("admin:aed_aedimportrun_changelist"))
        return HttpResponseRedirect(reverse("admin:aed_datastandard_changelist"))


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

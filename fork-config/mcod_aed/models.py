"""Data standards and the "Standard danych" link of datasets (DEC-015).

Models for aggregation (`AedImportRun`, `AedSourceRecord`, `AedDevice`) are added in T13.
"""
from django.contrib.postgres.fields import JSONField
from django.db import models


class DataStandard(models.Model):
    """A structured data standard a dataset can belong to (e.g. `aed-pl`)."""

    code = models.SlugField("kod", max_length=50, unique=True)
    name = models.CharField("nazwa", max_length=200)
    version = models.CharField("wersja", max_length=20)
    description = models.TextField("opis", blank=True)
    json_schema = JSONField("JSON Schema", default=dict, blank=True)
    # DEC-019: the standard as data (see spec.py); filled from standards/*.json by `aed_load_standard`
    fields = JSONField("pola (definicja)", default=list, blank=True,
                       help_text="Lista pól: name, label, type, obligation, allowed_values, pattern, minimum, "
                                 "maximum, max_length, synonyms, derivable.")
    merge = JSONField("reguła scalania", default=dict, blank=True,
                      help_text='{"strategy": "key", "keys": [["regon", "nazwa"], ...]} albo {"strategy": "geo"}')
    discovery = JSONField("wyszukiwanie w dane.gov.pl", default=dict, blank=True)
    publish = JSONField("publikacja zbioru zbiorczego", default=dict, blank=True)
    target_dataset = models.ForeignKey(
        "datasets.Dataset",
        verbose_name="zbiór zbiorczy",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Zbiór, do którego agregowane są dane wszystkich zbiorów w tym standardzie.",
    )
    max_invalid_ratio = models.FloatField(
        "maks. odsetek błędnych wierszy",
        default=0.2,
        help_text="Powyżej tego odsetka błędnych wierszy zasób jest blokowany (nie publikowany).",
    )
    is_active = models.BooleanField("aktywny", default=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "standard danych"
        verbose_name_plural = "standardy danych"
        ordering = ("name",)

    def __str__(self):
        return "{} ({} v{})".format(self.name, self.code, self.version)

    def as_api_dict(self):
        return {"code": self.code, "name": self.name, "version": self.version}

    def spec(self):
        from mcod.aed.spec import StandardSpec

        return StandardSpec.from_model(self)


class DatasetStandard(models.Model):
    """'Standard danych' of a dataset: the dataset is part of the standard's bigger dataset."""

    dataset = models.OneToOneField(
        "datasets.Dataset", on_delete=models.CASCADE, related_name="aed_standard_link"
    )
    standard = models.ForeignKey(DataStandard, on_delete=models.PROTECT, related_name="dataset_links")
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "standard danych zbioru"
        verbose_name_plural = "standardy danych zbiorów"

    def __str__(self):
        return "{} -> {}".format(self.dataset_id, self.standard.code)


class ResourceStandardValidation(models.Model):
    """Latest automatic validation of a resource against its dataset's standard (filled in T14)."""

    STATUS_VALID = "valid"
    STATUS_WARNINGS = "warnings"
    STATUS_INVALID = "invalid"
    STATUS_ERROR = "error"
    STATUS_CHOICES = (
        (STATUS_VALID, "zgodny ze standardem"),
        (STATUS_WARNINGS, "zgodny, z ostrzeżeniami"),
        (STATUS_INVALID, "niezgodny ze standardem"),
        (STATUS_ERROR, "nie udało się sprawdzić"),
    )

    resource = models.OneToOneField(
        "resources.Resource", on_delete=models.CASCADE, related_name="aed_standard_validation"
    )
    standard = models.ForeignKey(DataStandard, on_delete=models.CASCADE, related_name="validations")
    standard_version = models.CharField(max_length=20)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    blocking = models.BooleanField(default=False)
    blocking_reasons = JSONField(default=list, blank=True)
    data_format = models.CharField(max_length=20, blank=True)
    rows_total = models.PositiveIntegerField(default=0)
    rows_invalid = models.PositiveIntegerField(default=0)
    column_mapping = JSONField(default=dict, blank=True)
    coverage = JSONField(default=dict, blank=True)
    errors = JSONField(default=list, blank=True)
    warnings = JSONField(default=list, blank=True)
    validated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "walidacja zasobu względem standardu"
        verbose_name_plural = "walidacje zasobów względem standardu"

    def __str__(self):
        return "{}: {}".format(self.resource_id, self.status)

    def as_api_attributes(self):
        return {
            "resource_id": self.resource_id,
            "standard": self.standard.as_api_dict(),
            "standard_version": self.standard_version,
            "status": self.status,
            "status_label": self.get_status_display(),
            "valid": self.status == self.STATUS_VALID,
            "blocking": self.blocking,
            "blocking_reasons": self.blocking_reasons,
            "format": self.data_format or None,
            "rows_total": self.rows_total,
            "rows_invalid": self.rows_invalid,
            "column_mapping": self.column_mapping,
            "coverage": self.coverage,
            "errors": self.errors,
            "warnings": self.warnings,
            "validated_at": self.validated_at.strftime("%Y-%m-%dT%H:%M:%SZ") if self.validated_at else None,
        }


# --- Aggregation (T13) -----------------------------------------------------------------------


class AedImportRun(models.Model):
    """One run of "Agregacja AED" (command, Celery task or admin button)."""

    STATUS_RUNNING = "running"
    STATUS_OK = "ok"
    STATUS_ERROR = "error"
    STATUS_CHOICES = ((STATUS_RUNNING, "w toku"), (STATUS_OK, "zakończona"), (STATUS_ERROR, "błąd"))

    standard = models.ForeignKey(DataStandard, on_delete=models.CASCADE, related_name="runs")
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_RUNNING)
    triggered_by = models.CharField(max_length=100, blank=True)
    sources_count = models.PositiveIntegerField(default=0)
    records_count = models.PositiveIntegerField(default=0)
    devices_count = models.PositiveIntegerField(default=0)
    report = JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "agregacja AED"
        verbose_name_plural = "agregacje AED"
        ordering = ("-started_at",)

    def __str__(self):
        return "Agregacja {} ({})".format(self.started_at.strftime("%Y-%m-%d %H:%M") if self.started_at else "-", self.status)


class AedDevice(models.Model):
    """One AED of the common dataset (merged from all sources)."""

    standard = models.ForeignKey(DataStandard, on_delete=models.CASCADE, related_name="devices")
    id_aed = models.CharField(max_length=64, unique=True)
    data = JSONField(default=dict)
    lat = models.FloatField()
    lon = models.FloatField()
    sources_count = models.PositiveSmallIntegerField(default=1)
    sources = JSONField(default=list, blank=True)  # [{nazwa, typ, url, dataset_id}]

    class Meta:
        verbose_name = "urządzenie AED (zbiór zbiorczy)"
        verbose_name_plural = "urządzenia AED (zbiór zbiorczy)"

    def __str__(self):
        return "{} {}".format(self.id_aed, self.data.get("nazwa", ""))


class AedSourceRecord(models.Model):
    """One row of a source resource converted to the standard structure."""

    resource = models.ForeignKey("resources.Resource", on_delete=models.CASCADE, related_name="aed_records")
    dataset_id = models.IntegerField(db_index=True)
    row_id = models.CharField(max_length=120)
    data = JSONField(default=dict)
    lat = models.FloatField(null=True, blank=True)
    lon = models.FloatField(null=True, blank=True)
    valid = models.BooleanField(default=True)
    quality_flags = JSONField(default=list, blank=True)
    device = models.ForeignKey(AedDevice, null=True, blank=True, on_delete=models.SET_NULL, related_name="records")

    class Meta:
        verbose_name = "rekord źródłowy AED"
        verbose_name_plural = "rekordy źródłowe AED"

"""Models for harvested AED sources (T02); normalized/merged records come in T03."""

from django.db import models


class SourceDataset(models.Model):
    """A dataset harvested from an external source (dane.gov.pl dataset or OSM extract)."""

    class Kind(models.TextChoices):
        DANE_GOV_PL = "dane_gov_pl", "dane.gov.pl"
        OSM = "osm", "OpenStreetMap"

    kind = models.CharField(max_length=20, choices=Kind.choices)
    external_id = models.CharField(max_length=100)
    title = models.CharField(max_length=500)
    publisher = models.CharField(max_length=500, blank=True)
    url = models.URLField(max_length=500, blank=True, help_text="Human-readable page")
    api_url = models.URLField(max_length=500, blank=True)
    license_name = models.CharField(max_length=200, blank=True)
    source_modified = models.DateTimeField(null=True, blank=True)
    harvested_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["kind", "title"]
        constraints = [
            models.UniqueConstraint(fields=["kind", "external_id"], name="uniq_source_dataset")
        ]

    def __str__(self) -> str:
        return f"{self.get_kind_display()}: {self.title}"


class SourceResource(models.Model):
    """One downloadable resource (file) of a source dataset, with its raw payload."""

    class FetchStatus(models.TextChoices):
        PENDING = "pending", "pending"
        OK = "ok", "ok"
        ERROR = "error", "error"
        NOT_MACHINE_READABLE = "not_machine_readable", "not machine-readable"
        DUPLICATE = "duplicate", "duplicate URL"
        REQUIRES_API_KEY = "requires_api_key", "requires API key"

    dataset = models.ForeignKey(SourceDataset, on_delete=models.CASCADE, related_name="resources")
    external_id = models.CharField(max_length=100)
    title = models.CharField(max_length=500, blank=True)
    format = models.CharField(max_length=20, blank=True)
    url = models.URLField(max_length=1000)
    content_type = models.CharField(max_length=200, blank=True)
    raw = models.BinaryField(null=True, blank=True, editable=False)
    size = models.PositiveIntegerField(default=0)
    fetch_status = models.CharField(
        max_length=30, choices=FetchStatus.choices, default=FetchStatus.PENDING
    )
    fetch_error = models.TextField(blank=True)
    fetched_at = models.DateTimeField(null=True, blank=True)
    selected = models.BooleanField(
        default=False, help_text="Best machine-readable resource of the dataset (used for parsing)"
    )
    parse_status = models.CharField(max_length=20, blank=True)
    parse_error = models.TextField(blank=True)
    record_count = models.PositiveIntegerField(default=0)
    coverage = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["dataset", "external_id"]
        constraints = [
            models.UniqueConstraint(fields=["dataset", "external_id"], name="uniq_source_resource")
        ]

    def __str__(self) -> str:
        return f"{self.dataset.title} [{self.format}] #{self.external_id}"


class AED(models.Model):
    """National merged AED record in the standard schema (``data`` keyed by schema fields)."""

    id_aed = models.CharField(max_length=64, unique=True)
    lat = models.FloatField()
    lon = models.FloatField()
    data = models.JSONField(default=dict)
    sources_count = models.PositiveSmallIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id_aed"]
        indexes = [models.Index(fields=["lat", "lon"])]
        verbose_name = "AED"
        verbose_name_plural = "AED"

    def __str__(self) -> str:
        return f"{self.id_aed} {self.data.get('nazwa', '')}"


class SourceRecord(models.Model):
    """One AED from one source resource, normalized to the standard schema."""

    resource = models.ForeignKey(SourceResource, on_delete=models.CASCADE, related_name="records")
    source_row_id = models.CharField(max_length=100)
    raw = models.JSONField(default=dict)
    data = models.JSONField(default=dict)
    lat = models.FloatField(null=True, blank=True)
    lon = models.FloatField(null=True, blank=True)
    valid = models.BooleanField(default=True, help_text="Has usable coordinates inside Poland")
    quality_flags = models.JSONField(default=list, blank=True)
    aed = models.ForeignKey(
        AED, on_delete=models.SET_NULL, null=True, blank=True, related_name="source_records"
    )

    class Meta:
        ordering = ["resource", "source_row_id"]
        constraints = [
            models.UniqueConstraint(fields=["resource", "source_row_id"], name="uniq_source_record")
        ]

    def __str__(self) -> str:
        return f"{self.resource} row {self.source_row_id}"

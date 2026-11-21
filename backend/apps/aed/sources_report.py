"""Build the per-source report (reference scope / coverage) for ``GET /api/sources/``."""

from collections import Counter

from django.db.models import Max

from apps.aed.models import AED, SourceDataset, SourceRecord
from apps.aed.schema import SCHEMA_VERSION

STATUS_ORDER = ("ok", "requires_api_key", "not_machine_readable", "error", "duplicate", "pending")


def build_report() -> dict:
    sources = []
    for ds in SourceDataset.objects.prefetch_related("resources").order_by("kind", "title"):
        resources = list(ds.resources.all().defer("raw"))
        selected = next((r for r in resources if r.selected), None)
        if selected:
            status, note = "ok", ""
        else:
            ranked = sorted(resources, key=lambda r: STATUS_ORDER.index(r.fetch_status)
                            if r.fetch_status in STATUS_ORDER else 99)
            status = ranked[0].fetch_status if ranked else "pending"
            note = ranked[0].fetch_error if ranked else ""
        records = (
            SourceRecord.objects.filter(resource=selected).only("valid", "quality_flags", "aed")
            if selected else SourceRecord.objects.none()
        )
        flags: Counter = Counter()
        valid = confirmed = 0
        for rec in records.select_related("aed").only(
            "valid", "quality_flags", "aed__sources_count"
        ):
            flags.update(rec.quality_flags)
            valid += rec.valid
            confirmed += bool(rec.aed and rec.aed.sources_count > 1)
        sources.append(
            {
                "id": f"{ds.kind}:{ds.external_id}",
                "title": ds.title,
                "publisher": ds.publisher,
                "kind": ds.kind,
                "url": ds.url,
                "license_name": ds.license_name,
                "format": selected.format if selected else "",
                "status": status,
                "status_note": note,
                "resources_count": len(resources),
                "record_count": selected.record_count if selected else 0,
                "valid_count": valid,
                "confirmed_by_other_sources": confirmed,
                "coverage": selected.coverage if selected and selected.coverage else None,
                "quality_flags": dict(flags.most_common()),
            }
        )
    return {
        "aed_count": AED.objects.count(),
        "multi_source_aed_count": AED.objects.filter(sources_count__gt=1).count(),
        "record_count": SourceRecord.objects.count(),
        "updated_at": AED.objects.aggregate(m=Max("updated_at"))["m"],
        "schema_version": SCHEMA_VERSION,
        "sources": sources,
    }




"""Aggregation inside the portal (T13, DEC-014/015/016).

All published, non-blocked resources of datasets whose "Standard danych" is aed-pl (files and
connected APIs) -> converted to the standard (AedSourceRecord, invalid rows excluded) -> merged
(AedDevice, DEC-011 rules) -> published as the common dataset "Defibrylatory AED – zbiór ogólnopolski"
with portal-generated CSV (table + map), XLSX, GeoJSON, schema XLSX and an API link.
"""
import logging
from collections import Counter

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from mcod.aed import connectors, exports, merge, normalize, parsers, publishing, schema_export, validation
from mcod.aed.standards import AED_STANDARD_CODE

logger = logging.getLogger("mcod")

NATIONAL_EXT = "aed-pl-national"
NATIONAL_TITLE = "Defibrylatory AED – zbiór ogólnopolski"
NATIONAL_CSV_EXT = "aed-national-csv"
NATIONAL_ORG = "Misja AED"
OSM_MARKERS = ("openaedmap.org", "openstreetmap")


def _is_osm(resource):
    link = (resource.link or "").lower()
    return any(m in link for m in OSM_MARKERS) or (resource.dataset.ext_ident or "").startswith("osm-")


def portal_dataset_url(dataset):
    return "{}/pl/dataset/{},{}".format(settings.BASE_URL, dataset.pk, dataset.slug)


def source_resources(standard):
    """Published, non-blocked resources of published datasets in the standard (not the target)."""
    from mcod.resources.models import Resource

    qs = (
        Resource.raw.filter(
            dataset__aed_standard_link__standard=standard,
            dataset__status="published",
            dataset__is_removed=False,
            status="published",
            is_removed=False,
        )
        .exclude(aed_standard_validation__blocking=True)
        .select_related("dataset", "dataset__organization")
        .order_by("dataset_id", "position", "id")
    )
    if standard.target_dataset_id:
        qs = qs.exclude(dataset_id=standard.target_dataset_id)
    return list(qs)


def convert_resource(resource, max_invalid_ratio):
    """-> (list[merge.Rec], source report dict)."""
    dataset = resource.dataset
    osm = _is_osm(resource)
    entry = {
        "dataset_id": dataset.pk, "dataset_title": dataset.title,
        "institution": dataset.organization.title if dataset.organization_id else "",
        "resource_id": resource.pk, "resource_title": resource.title,
        "kind": "api" if resource.link and not resource.is_link_internal else "file",
        "source_type": "osm" if osm else "official",
        "url": portal_dataset_url(dataset), "original_url": dataset.url or "",
    }
    try:
        raw, filename, fmt = connectors.resource_bytes(resource)
        fmt = validation.detect_format(raw, filename=filename, hint=fmt)
        rows = parsers.parse(fmt, raw)
    except Exception as exc:  # unreadable source: reported, run continues
        entry.update(status="error", error=str(exc)[:500], rows=0, records=0, excluded_rows=0, coverage={})
        return [], entry
    if filename == connectors.WARSAW_SNAPSHOT_NAME:
        entry["note"] = ("API m.st. Warszawy niedostępne z tego serwera – użyto oznaczonej kopii offline "
                         "z 2026-11-21 (pobranej wcześniej przez to samo API z tokenem).")
        entry["offline_copy"] = True
    report = validation.validate_rows(rows, max_invalid_ratio=max_invalid_ratio, fmt=fmt, collect_invalid=True)
    invalid = report.pop("_invalid_rows")
    ctx = normalize.SourceContext(
        kind="osm" if osm else "dane_gov_pl",
        key="osm" if osm else (dataset.ext_ident or "ds{}".format(dataset.pk)),
        name="OpenStreetMap" if osm else entry["institution"] or dataset.title,
        url=entry["url"],
        updated=resource.data_date,
    )
    recs, seen = [], set()
    for index, row in enumerate(rows, start=1):
        result = normalize.normalize_row(row, ctx)
        row_id = str(row.row_id or index)
        while row_id in seen:
            row_id += "+"
        seen.add(row_id)
        rec = merge.Rec(
            resource_id=resource.pk, kind="osm" if osm else "official", source_key="r{}".format(resource.pk),
            row_id=row_id[:120], data=result.data, lat=result.lat, lon=result.lon,
            valid=result.valid and index not in invalid, flags=list(result.flags),
        )
        if index in invalid and result.valid:
            rec.flags.append("wiersz_niezgodny_ze_standardem")
        recs.append(rec)
    if not osm:
        merge.flag_coordinate_problems(recs)
    included = [r for r in recs if r.valid]
    flags = Counter(f for r in recs for f in r.flags)
    entry.update(
        status="ok", format=fmt, rows=len(rows), records=len(included), excluded_rows=len(rows) - len(included),
        validation_status=report["status"], validation_valid=report["valid"],
        coverage=normalize.coverage([r.data for r in included]), quality_flags=dict(flags.most_common()),
    )
    return recs, entry


def _sources_of(group, entries_by_resource):
    out, seen = [], set()
    for rec in group:
        entry = entries_by_resource[rec.resource_id]
        key = entry["dataset_id"]
        if key in seen:
            continue
        seen.add(key)
        url = rec.data.get("zrodlo_url") if rec.kind == "osm" else entry["url"]
        out.append({
            "nazwa": "OpenStreetMap" if rec.kind == "osm" else entry["institution"] or entry["dataset_title"],
            "typ": "osm" if rec.kind == "osm" else "dane_gov_pl",
            "url": url, "dataset_id": entry["dataset_id"],
        })
    return out


def ensure_national_dataset(standard):
    org, _ = publishing.ensure_organization(NATIONAL_ORG, institution_type="other", website=settings.BASE_URL + "/")
    from mcod.datasets.models import Dataset

    existing = Dataset.raw.filter(ext_ident=NATIONAL_EXT, is_removed=False).first() or Dataset.raw.filter(
        title=NATIONAL_TITLE, is_removed=False).first()
    if existing is not None and existing.ext_ident != NATIONAL_EXT:
        Dataset.raw.filter(pk=existing.pk).update(ext_ident=NATIONAL_EXT)
    notes = (
        "<p>Ogólnopolski zbiór defibrylatorów AED tworzony <strong>wewnątrz portalu</strong> przez agregację "
        "wszystkich zbiorów oznaczonych standardem danych <strong>„Dane AED” (aed-pl)</strong> – plików "
        "instytucji i połączonych API (m.st. Warszawa, OpenStreetMap). Każdy zasób jest automatycznie "
        "walidowany ze wzorcowym zakresem danych; zasoby zablokowane i błędne wiersze są pomijane, rekordy "
        "z różnych źródeł opisujące ten sam AED są scalane (≤ 25 m lub ≤ 75 m i podobna nazwa/adres).</p>"
        "<p>Każdy rekord wskazuje źródło (kolumny <code>zrodlo</code>, <code>zrodlo_url</code>). API: "
        "<code>/1.4/aed/devices</code> (GeoJSON), <code>/1.4/aed/sources</code> (źródła i pokrycie), "
        "<code>/1.4/aed/validate</code> (walidacja danych), <code>/1.4/aed/schema</code> (standard).</p>"
    )
    dataset, _ = publishing.ensure_dataset(
        org, NATIONAL_TITLE, NATIONAL_EXT, notes, standard=None,
        tags=("AED", "defibrylatory", "zdrowie", "ratownictwo"), license_name="CC BY-SA 4.0",
        license_text=exports.LICENSE + " Wymagane uznanie autorstwa; bazy pochodne na tej samej licencji (ODbL).",
        update_frequency="daily", url=settings.API_URL + "/1.4/aed/sources",
    )
    if standard.target_dataset_id != dataset.pk:
        standard.target_dataset = dataset
        standard.save(update_fields=["target_dataset", "modified"])
    return dataset


def publish_national(standard, devices, run):
    dataset = ensure_national_dataset(standard)
    meta = exports.metadata(run, len(devices))
    files = [
        (NATIONAL_CSV_EXT, "Defibrylatory AED – Polska (CSV)", "defibrylatory-aed-polska.csv", exports.csv_bytes(devices), "csv",
         "Pełny zbiór w formacie CSV (UTF-8), kolumny zgodne ze wzorcowym zakresem danych AED. Podgląd tabeli i mapy."),
        ("aed-national-xlsx", "Defibrylatory AED – Polska (XLSX)", "defibrylatory-aed-polska.xlsx", exports.xlsx_bytes(devices, meta), "xlsx",
         "Pełny zbiór w formacie XLSX z arkuszem metadanych."),
        ("aed-national-geojson", "Defibrylatory AED – Polska (GeoJSON)", "defibrylatory-aed-polska.geojson", exports.geojson_bytes(devices, meta), "geojson",
         "Pełny zbiór jako GeoJSON FeatureCollection (WGS84)."),
        ("aed-standard-xlsx", "Wzorcowy zakres danych AED (schemat, XLSX)", "wzorcowy-zakres-danych-aed.xlsx", schema_export.xlsx_bytes(), "xlsx",
         "Specyfikacja standardu „Dane AED” (aed-pl): pola, typy, wymagalność, opisy, dozwolone wartości."),
    ]
    actions = {}
    titles_by_ext = {f[0]: f[1] for f in files}
    _adopt_existing_resources(dataset, titles_by_ext)
    for position, (ext, title, filename, content, fmt, description) in enumerate(files, start=1):
        res, action = publishing.ensure_file_resource(dataset, ext, title, description, filename, content, fmt=fmt,
                                                      position=position)
        actions[ext] = {"resource_id": res.pk, "action": action}
    _adopt_existing_resources(dataset, {"aed-national-api": "Defibrylatory AED – API zgodne z dane.gov.pl (JSON)"})
    res, action = publishing.ensure_api_resource(
        dataset, "aed-national-api", "Defibrylatory AED – API portalu (GeoJSON, /1.4/aed/devices)",
        "Dane zbioru na żywo przez API portalu: /1.4/aed/devices (GeoJSON), /1.4/aed/sources (źródła), "
        "/1.4/aed/validate (walidacja danych względem standardu).",
        settings.API_URL + "/1.4/aed/devices", position=len(files) + 1,
    )
    actions["aed-national-api"] = {"resource_id": res.pk, "action": action}
    return dataset, actions


def _adopt_existing_resources(dataset, titles_by_ext):
    """Resources published earlier without ext_ident (T06 script) are reused, not duplicated."""
    from mcod.resources.models import Resource

    for ext, title in titles_by_ext.items():
        if Resource.raw.filter(dataset=dataset, ext_ident=ext, is_removed=False).exists():
            continue
        old = Resource.raw.filter(dataset=dataset, title=title, is_removed=False).filter(ext_ident__in=["", None]).first()
        if old is not None:
            Resource.raw.filter(pk=old.pk).update(ext_ident=ext)


def run_aggregation(triggered_by="command", publish=True, standard=None):
    from mcod.aed.models import AedDevice, AedImportRun, AedSourceRecord, DataStandard
    from mcod.aed.standards import ensure_aed_standard

    if standard is None:
        standard = DataStandard.objects.filter(code=AED_STANDARD_CODE).first() or ensure_aed_standard()
    run = AedImportRun.objects.create(standard=standard, triggered_by=triggered_by[:100])
    try:
        resources = source_resources(standard)
        all_recs, entries = [], []
        for resource in resources:
            recs, entry = convert_resource(resource, standard.max_invalid_ratio)
            all_recs.extend(recs)
            entries.append(entry)
        entries_by_resource = {e["resource_id"]: e for e in entries}
        merged = merge.merge(all_recs)
        with transaction.atomic():
            AedSourceRecord.objects.filter(device__standard=standard).delete()
            AedSourceRecord.objects.filter(resource_id__in=[e["resource_id"] for e in entries]).delete()
            AedDevice.objects.filter(standard=standard).delete()
            devices = AedDevice.objects.bulk_create([
                AedDevice(standard=standard, id_aed=id_aed, lat=lat, lon=lon, data=data, sources_count=len(group),
                          sources=_sources_of(group, entries_by_resource))
                for id_aed, lat, lon, data, group in merged
            ], batch_size=2000)
            device_by_rec = {}
            for device, (_, _, _, _, group) in zip(devices, merged):
                for rec in group:
                    device_by_rec[id(rec)] = device
            dataset_of = {e["resource_id"]: e["dataset_id"] for e in entries}
            AedSourceRecord.objects.bulk_create([
                AedSourceRecord(resource_id=r.resource_id, dataset_id=dataset_of[r.resource_id], row_id=r.row_id,
                                data=r.data, lat=r.lat, lon=r.lon, valid=r.valid, quality_flags=r.flags,
                                device=device_by_rec.get(id(r)))
                for r in all_recs
            ], batch_size=2000)
        devices = list(AedDevice.objects.filter(standard=standard).order_by("id_aed"))
        report = {
            "standard": standard.as_api_dict(),
            "sources": entries,
            "records": len(all_recs),
            "records_included": sum(1 for r in all_recs if r.valid),
            "devices": len(devices),
            "multi_source_devices": sum(1 for d in devices if d.sources_count > 1),
        }
        if publish:
            dataset, actions = publish_national(standard, devices, run)
            report["national_dataset"] = {"id": dataset.pk, "title": dataset.title, "url": portal_dataset_url(dataset),
                                          "resources": actions}
        run.status = AedImportRun.STATUS_OK
        run.sources_count = len(entries)
        run.records_count = len(all_recs)
        run.devices_count = len(devices)
        run.report = report
        run.finished_at = timezone.now()
        run.save()
        logger.info("mcod.aed: aggregation %s finished: %s sources, %s records, %s devices",
                    run.pk, len(entries), len(all_recs), len(devices))
        return run
    except Exception as exc:
        logger.exception("mcod.aed: aggregation failed")
        run.status = AedImportRun.STATUS_ERROR
        run.report = {"error": str(exc)[:2000]}
        run.finished_at = timezone.now()
        run.save()
        raise

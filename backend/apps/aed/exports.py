"""Machine-readable exports of the national AED dataset (T04): CSV, JSON, GeoJSON, XLSX.

All exports use the standard schema column order (``apps.aed.schema.FIELDS``) and share one
metadata block. The merged database contains OpenStreetMap data, so it is published under
ODbL 1.0 (share-alike); official municipal sources are CC0 / CC BY and compatible with it.
"""

from __future__ import annotations

import csv
import io
import json
from datetime import UTC, datetime

from django.core.cache import cache
from django.db.models import Max
from openpyxl import Workbook

from apps.aed.models import AED, SourceDataset
from apps.aed.schema import FIELD_NAMES, SCHEMA_NAME, SCHEMA_VERSION
from apps.aed.schema_export import format_value

DATASET_TITLE = "Defibrylatory AED – zbiór ogólnopolski"
DATASET_SLUG = "defibrylatory-aed-zbior-ogolnopolski"
DATASET_NOTES = (
    "Ogólnopolski zbiór lokalizacji automatycznych defibrylatorów zewnętrznych (AED), "
    "zintegrowany automatycznie ze wszystkich zbiorów o AED opublikowanych w portalu "
    "dane.gov.pl oraz z OpenStreetMap, ujednolicony do wzorcowego zakresu danych "
    f"({SCHEMA_NAME} {SCHEMA_VERSION}). Każdy rekord wskazuje źródła, z których pochodzi."
)
PUBLISHER = "Misja AED (prototyp hackathonowy)"
LICENSE_NAME = "ODbL 1.0"
LICENSE_URL = "https://opendatacommons.org/licenses/odbl/1-0/"
LICENSE_NOTE = (
    "Zbiór zawiera dane z OpenStreetMap (© współtwórcy OpenStreetMap, ODbL 1.0), dlatego "
    "całość udostępniana jest na licencji ODbL 1.0. Dane gmin: CC0 1.0 / CC BY 4.0 "
    "(zgodnie z licencjami zbiorów źródłowych)."
)
UPDATE_FREQUENCY = "Codziennie"
KEYWORDS = ["aed", "defibrylatory", "defibrylator", "zdrowie", "ratownictwo", "pierwsza pomoc"]

XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
CSV_CONTENT_TYPE = "text/csv; charset=utf-8"
JSON_CONTENT_TYPE = "application/json; charset=utf-8"
GEOJSON_CONTENT_TYPE = "application/geo+json; charset=utf-8"


def data_version() -> str:
    """Cache key component that changes whenever the merged dataset is rebuilt."""
    agg = AED.objects.aggregate(m=Max("updated_at"))
    return f"{AED.objects.count()}-{agg['m'].timestamp() if agg['m'] else 0}"


def last_modified() -> datetime | None:
    return AED.objects.aggregate(m=Max("updated_at"))["m"]


def rows() -> list[dict]:
    """All AEDs as dicts in standard column order (missing values = None)."""
    return [
        {name: data.get(name) for name in FIELD_NAMES}
        for data in AED.objects.order_by("id_aed").values_list("data", flat=True)
    ]


def sources_metadata() -> list[dict]:
    result = []
    for ds in SourceDataset.objects.order_by("kind", "title"):
        selected = ds.resources.filter(selected=True).defer("raw").first()
        result.append(
            {
                "tytul": ds.title,
                "dysponent": ds.publisher,
                "url": ds.url,
                "licencja": ds.license_name,
                "rekordy": selected.record_count if selected else 0,
            }
        )
    return result


def metadata() -> dict:
    modified = last_modified()
    return {
        "tytul": DATASET_TITLE,
        "opis": DATASET_NOTES,
        "dysponent": PUBLISHER,
        "licencja": LICENSE_NAME,
        "licencja_url": LICENSE_URL,
        "licencja_uwagi": LICENSE_NOTE,
        "schemat": f"{SCHEMA_NAME} {SCHEMA_VERSION}",
        "schemat_url": "/api/schema-standard/",
        "czestotliwosc_aktualizacji": UPDATE_FREQUENCY,
        "data_aktualizacji": modified.isoformat() if modified else None,
        "wygenerowano": datetime.now(UTC).isoformat(),
        "liczba_rekordow": AED.objects.count(),
        "zrodla": sources_metadata(),
    }


def _cached(kind: str, builder) -> bytes:
    key = f"aed-export:{kind}:{data_version()}"
    content = cache.get(key)
    if content is None:
        content = builder()
        cache.set(key, content, timeout=60 * 60)
    return content


def _build_csv() -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(FIELD_NAMES)
    for row in rows():
        writer.writerow([format_value(row[name]) for name in FIELD_NAMES])
    return buffer.getvalue().encode("utf-8")


def _build_json() -> bytes:
    payload = {"meta": metadata(), "data": rows()}
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def _build_geojson() -> bytes:
    features = [
        {
            "type": "Feature",
            "id": row["id_aed"],
            "geometry": {
                "type": "Point",
                "coordinates": [row["dlugosc_geograficzna"], row["szerokosc_geograficzna"]],
            },
            "properties": row,
        }
        for row in rows()
    ]
    payload = {"type": "FeatureCollection", "metadata": metadata(), "features": features}
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def _build_xlsx() -> bytes:
    wb = Workbook(write_only=True)
    ws = wb.create_sheet("Dane")
    ws.append(list(FIELD_NAMES))
    for row in rows():
        ws.append([row[name] if not isinstance(row[name], bool) else format_value(row[name])
                   for name in FIELD_NAMES])
    meta_ws = wb.create_sheet("Metadane")
    meta_ws.append(["Element", "Wartość"])
    for key, value in metadata().items():
        if key == "zrodla":
            for src in value:
                meta_ws.append(["źródło", f"{src['tytul']} ({src['dysponent']}) – {src['url']} – "
                                          f"{src['licencja']} – rekordów: {src['rekordy']}"])
        else:
            meta_ws.append([key, value])
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


EXPORTS = {
    "csv": (CSV_CONTENT_TYPE, _build_csv),
    "json": (JSON_CONTENT_TYPE, _build_json),
    "geojson": (GEOJSON_CONTENT_TYPE, _build_geojson),
    "xlsx": (XLSX_CONTENT_TYPE, _build_xlsx),
}


def export(fmt: str) -> tuple[bytes, str]:
    content_type, builder = EXPORTS[fmt]
    return _cached(fmt, builder), content_type


# --- lightweight GeoJSON for the Next.js map (contract DEC-008) ---------------------------

MAP_FIELDS = (
    "id_aed", "nazwa", "miejscowosc", "opis_lokalizacji", "w_budynku", "pietro", "dostep",
    "godziny_dostepnosci", "zabezpieczenie", "status", "dysponent", "telefon_kontaktowy",
    "data_aktualizacji",
)


def display_address(data: dict) -> str | None:
    street = " ".join(
        p for p in (data.get("cecha_ulicy") if data.get("cecha_ulicy") != "inne" else "",
                    data.get("nazwa_ulicy"), data.get("nr_budynku")) if p
    )
    if street and data.get("nr_lokalu"):
        street += f"/{data['nr_lokalu']}"
    city = " ".join(p for p in (data.get("kod_pocztowy"), data.get("miejscowosc")) if p)
    text = ", ".join(p for p in (street, city) if p)
    return text or None


def _map_sources() -> dict[int, list[dict]]:
    from apps.aed.models import SourceRecord

    result: dict[int, list[dict]] = {}
    qs = SourceRecord.objects.filter(aed__isnull=False).values_list(
        "aed_id", "resource__dataset__kind", "resource__dataset__publisher",
        "resource__dataset__title", "resource__dataset__url", "data__zrodlo_url",
    )
    for aed_id, kind, publisher, title, ds_url, rec_url in qs:
        entry = {
            "nazwa": "OpenStreetMap" if kind == "osm" else (publisher or title),
            "typ": kind,
            "url": rec_url or ds_url or None,
        }
        result.setdefault(aed_id, []).append(entry)
    for entries in result.values():
        entries.sort(key=lambda e: e["typ"] != "dane_gov_pl")
    return result


def map_features(aeds) -> list[dict]:
    sources = _map_sources()
    features = []
    for pk, lat, lon, data in aeds.values_list("pk", "lat", "lon", "data"):
        props = {name: data.get(name) for name in MAP_FIELDS}
        props["adres"] = display_address(data)
        props["zrodla"] = sources.get(pk, [])
        features.append(
            {"type": "Feature", "id": data.get("id_aed"),
             "geometry": {"type": "Point", "coordinates": [lon, lat]}, "properties": props}
        )
    return features


def map_geojson_all() -> bytes:
    def build() -> bytes:
        payload = {
            "type": "FeatureCollection",
            "meta": {"count": AED.objects.count(),
                     "generated_at": datetime.now(UTC).isoformat(),
                     "license": f"{LICENSE_NAME} – {LICENSE_NOTE}"},
            "features": map_features(AED.objects.order_by("id_aed")),
        }
        return json.dumps(payload, ensure_ascii=False).encode("utf-8")

    return _cached("map", build)

"""Tests for the dane.gov.pl-compatible API, exports and map GeoJSON (T04)."""

import csv
import io
import json
from pathlib import Path

import pytest
from django.core.cache import cache
from openpyxl import load_workbook
from rest_framework.test import APIClient

from apps.aed.models import AED, SourceDataset, SourceRecord, SourceResource
from apps.aed.schema import FIELD_NAMES

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def aeds(db):
    ds = SourceDataset.objects.create(kind="dane_gov_pl", external_id="39512",
                                      title="Lokalizacja defibrylatorów", publisher="Warszawa",
                                      url="https://dane.gov.pl/pl/dataset/39512")
    osm = SourceDataset.objects.create(kind="osm", external_id="openaedmap-pl", title="OSM")
    res = SourceResource.objects.create(dataset=ds, external_id="r", url="https://x.test",
                                        fetch_status="ok", selected=True, record_count=2)
    osm_res = SourceResource.objects.create(dataset=osm, external_id="o", url="https://o.test",
                                            fetch_status="ok", selected=True, record_count=1)
    a1 = AED.objects.create(id_aed="PL-AED-A", lat=52.2086, lon=21.0148, sources_count=2, data={
        "id_aed": "PL-AED-A", "nazwa": "Urząd Dzielnicy Mokotów", "szerokosc_geograficzna": 52.2086,
        "dlugosc_geograficzna": 21.0148, "miejscowosc": "Warszawa", "nazwa_ulicy": "Rakowiecka",
        "nr_budynku": "25/27", "kod_pocztowy": "02-517", "dostep": "publiczny",
        "w_budynku": True, "pietro": 0, "zrodlo": "Warszawa; OpenStreetMap",
        "data_aktualizacji": "2026-06-01",
    })
    a2 = AED.objects.create(id_aed="PL-AED-B", lat=53.1707, lon=18.0476, data={
        "id_aed": "PL-AED-B", "nazwa": "BCTW", "szerokosc_geograficzna": 53.1707,
        "dlugosc_geograficzna": 18.0476, "miejscowosc": "Bydgoszcz", "dostep": "nieznany",
        "zrodlo": "Warszawa", "data_aktualizacji": "2026-06-01",
    })
    SourceRecord.objects.create(resource=res, source_row_id="1", aed=a1, data={})
    SourceRecord.objects.create(resource=osm_res, source_row_id="node/1", aed=a1,
                                data={"zrodlo_url": "https://www.openstreetmap.org/node/1"})
    SourceRecord.objects.create(resource=res, source_row_id="2", aed=a2, data={})
    return a1, a2


def _get(path: str) -> dict:
    response = APIClient().get(path)
    assert response.status_code == 200, response.content[:300]
    return response.json()


# --- dane.gov.pl compatibility -----------------------------------------------------------


def _key_paths(node, prefix: str = "") -> set[str]:
    """All key paths of a JSON tree (colN collapsed, lists by first element)."""
    paths: set[str] = set()
    if isinstance(node, dict):
        for key, value in node.items():
            key = "colN" if key.startswith("col") and key[3:].isdigit() else key
            paths.add(f"{prefix}.{key}")
            paths |= _key_paths(value, f"{prefix}.{key}")
    elif isinstance(node, list) and node:
        paths |= _key_paths(node[0], f"{prefix}[]")
    return paths


VALUE_DEPENDENT = (".data.attributes.", ".data[].attributes.", ".meta.params.",
                   ".meta.aggregations.", ".links.next", ".links.prev")


@pytest.mark.parametrize(
    ("fixture", "path"),
    [
        ("danegov_dataset.json", "/api/1.4/datasets/1"),
        ("danegov_resource.json", "/api/1.4/resources/1"),
        ("danegov_dataset_resources.json", "/api/1.4/datasets/1/resources"),
        ("danegov_resource_data.json", "/api/1.4/resources/1/data?per_page=2"),
    ],
)
def test_envelope_matches_real_dane_gov_pl_api(aeds, fixture: str, path: str) -> None:
    real, ours = _fixture(fixture), _get(path)
    if "/data?" in path:  # full key tree must be identical for tabular data
        def strip(paths: set[str]) -> set[str]:
            return {p for p in paths if not p.startswith(VALUE_DEPENDENT)}
        assert strip(_key_paths(real)) == strip(_key_paths(ours))
        assert list(real["data"][0]) == list(ours["data"][0])  # same key order
    assert set(real) == set(ours)
    assert set(real["meta"]) <= set(ours["meta"])
    r = real["data"][0] if isinstance(real["data"], list) else real["data"]
    o = ours["data"][0] if isinstance(ours["data"], list) else ours["data"]
    assert set(r) <= set(o)
    assert set(r["relationships"]) <= set(o["relationships"])
    if "col1" not in r["attributes"]:
        assert set(r["attributes"]) <= set(o["attributes"])
    assert ours["jsonapi"] == {"version": "1.4"}


def test_dataset_detail(aeds) -> None:
    body = _get("/api/1.4/datasets/1")
    attrs = body["data"]["attributes"]
    assert attrs["title"] == "Defibrylatory AED – zbiór ogólnopolski"
    assert attrs["license_name"] == "ODbL 1.0"
    assert body["data"]["relationships"]["resources"]["meta"]["count"] == 5
    assert body["meta"]["path"] == "/1.4/datasets/1"


@pytest.mark.django_db
def test_dataset_slug_form_and_404() -> None:
    assert APIClient().get("/api/1.4/datasets/1,defibrylatory").status_code == 200
    assert APIClient().get("/api/1.4/datasets/999").status_code == 404
    assert APIClient().get("/api/1.4/resources/999").status_code == 404
    assert APIClient().get("/api/1.4/resources/5/data").status_code == 404  # schema xlsx


@pytest.mark.django_db
def test_dataset_list_search() -> None:
    assert _get("/api/1.4/datasets?q=defibrylatory")["meta"]["count"] == 1
    assert _get("/api/1.4/datasets?q=apteki")["meta"]["count"] == 0


def test_resources_point_to_exports(aeds) -> None:
    body = _get("/api/1.4/datasets/1/resources")
    formats = [r["attributes"]["format"] for r in body["data"]]
    assert formats == ["csv", "xlsx", "geojson", "json", "xlsx"]
    assert body["data"][0]["attributes"]["download_url"].endswith("/api/exports/aed.csv")
    assert "tabular_data" in body["data"][0]["relationships"]


def test_resource_data_rows_and_pagination(aeds) -> None:
    body = _get("/api/1.4/resources/1/data?per_page=1")
    assert body["meta"]["count"] == 2
    assert body["meta"]["headers_map"]["col1"] == "id_aed"
    assert len(body["meta"]["headers_map"]) == len(FIELD_NAMES)
    row = body["data"][0]
    assert row["type"] == "row" and row["meta"]["row_no"] == 1
    assert row["attributes"]["col1"] == {"repr": "PL-AED-A", "val": "PL-AED-A"}
    assert "next" in body["links"] and "prev" not in body["links"]
    assert "first" not in body["links"]  # api.dane.gov.pl does not return it
    page2 = _get("/api/1.4/resources/1/data?per_page=1&page=2")
    assert page2["data"][0]["attributes"]["col1"]["val"] == "PL-AED-B"
    assert "prev" in page2["links"]


def test_resource_data_search_and_single_row(aeds) -> None:
    body = _get("/api/1.4/resources/1/data?q=Bydgoszcz")
    assert body["meta"]["count"] == 1
    row_url = body["data"][0]["links"]["self"]
    single = _get(row_url.replace("http://testserver", ""))
    assert single["data"]["attributes"]["col1"]["val"] == "PL-AED-B"


# --- exports ------------------------------------------------------------------------------


def test_csv_export(aeds) -> None:
    response = APIClient().get("/api/exports/aed.csv")
    assert response["Content-Type"].startswith("text/csv")
    rows = list(csv.DictReader(io.StringIO(response.content.decode("utf-8"))))
    assert list(rows[0].keys()) == list(FIELD_NAMES)
    assert float(rows[0]["szerokosc_geograficzna"]) == pytest.approx(52.2086)
    assert rows[0]["w_budynku"] == "true"


def test_json_and_geojson_exports(aeds) -> None:
    data = json.loads(APIClient().get("/api/exports/aed.json").content)
    assert data["meta"]["liczba_rekordow"] == 2 and data["meta"]["licencja"] == "ODbL 1.0"
    assert len(data["meta"]["zrodla"]) == 2
    geo = json.loads(APIClient().get("/api/exports/aed.geojson").content)
    assert geo["type"] == "FeatureCollection" and len(geo["features"]) == 2
    assert geo["features"][0]["geometry"]["coordinates"] == [21.0148, 52.2086]


def test_xlsx_export(aeds) -> None:
    wb = load_workbook(io.BytesIO(APIClient().get("/api/exports/aed.xlsx").content))
    assert wb.sheetnames == ["Dane", "Metadane"]
    assert [c.value for c in wb["Dane"][1]] == list(FIELD_NAMES)
    assert wb["Dane"].max_row == 3


@pytest.mark.django_db
def test_unknown_export_404() -> None:
    assert APIClient().get("/api/exports/aed.pdf").status_code == 404


def test_export_cache_invalidated_after_rebuild(aeds) -> None:
    first = APIClient().get("/api/exports/aed.csv").content
    AED.objects.filter(id_aed="PL-AED-B").delete()
    second = APIClient().get("/api/exports/aed.csv").content
    assert first != second and second.count(b"\n") == 2


# --- map GeoJSON (DEC-008 contract) ------------------------------------------------------


def test_map_geojson_contract(aeds) -> None:
    body = json.loads(APIClient().get("/api/aed/").content)
    assert body["meta"]["count"] == 2
    feature = next(f for f in body["features"] if f["id"] == "PL-AED-A")
    props = feature["properties"]
    for key in ("id_aed", "nazwa", "adres", "miejscowosc", "opis_lokalizacji", "w_budynku",
                "pietro", "dostep", "godziny_dostepnosci", "zabezpieczenie", "status",
                "dysponent", "telefon_kontaktowy", "data_aktualizacji", "zrodla"):
        assert key in props
    assert props["adres"] == "Rakowiecka 25/27, 02-517 Warszawa"
    assert props["opis_lokalizacji"] is None
    assert [s["typ"] for s in props["zrodla"]] == ["dane_gov_pl", "osm"]
    assert props["zrodla"][1]["url"] == "https://www.openstreetmap.org/node/1"


def test_map_filters(aeds) -> None:
    by_q = json.loads(APIClient().get("/api/aed/?q=mokot").content)
    assert [f["id"] for f in by_q["features"]] == ["PL-AED-A"]
    by_bbox = json.loads(APIClient().get("/api/aed/?bbox=17.9,53.1,18.1,53.2").content)
    assert [f["id"] for f in by_bbox["features"]] == ["PL-AED-B"]
    assert APIClient().get("/api/aed/?bbox=oops").status_code == 400


def test_map_is_gzipped(aeds) -> None:
    response = APIClient().get("/api/aed/", HTTP_ACCEPT_ENCODING="gzip")
    assert response.get("Content-Encoding") == "gzip"


BROWSER_ACCEPT = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"


@pytest.mark.parametrize(
    "path",
    ["/api/1.4/datasets/1", "/api/1.4/resources/1/data?per_page=2", "/api/aed/?q=bydgoszcz",
     "/api/aed/", "/api/sources/", "/api/schema-standard/"],
)
def test_browser_gets_raw_json_not_html(aeds, path: str) -> None:
    """Like api.dane.gov.pl: a browser (Accept: text/html) must receive parseable JSON."""
    response = APIClient().get(path, HTTP_ACCEPT=BROWSER_ACCEPT)
    assert response.status_code == 200
    assert "html" not in response["Content-Type"]
    assert json.loads(response.content)

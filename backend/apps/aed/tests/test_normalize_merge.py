"""Tests for parsing, normalization, coverage, merge and the sources report (T03)."""

import io
import json
from datetime import date

import pytest
from openpyxl import Workbook
from rest_framework.test import APIClient

from apps.aed import merge, normalize, parsers
from apps.aed.models import AED, SourceDataset, SourceRecord, SourceResource

KROSNO = (
    "Długość geograficzna,Szerokość geograficzna, Nazwa, Lokalizacja, Adres, Numer Id\r\n"
    '21.72034402175176,49.718809346153336,"Defibrylator","Zespół  Krytych Pływalni",'
    '"ul. Jasna, 38-400 Krosno","1"\r\n'
).encode()
MARKI = (
    '"Długość geograficzna,Szerokość geograficzna, Nazwa, Lokalizacja, Adres, Numer Id"\r\n'
    '"52.326697, 21.107557,""Defibrylator"",""Urząd Miasta Marki "",'
    '""Al.. Piłsudskiego 95, 05-270 Marki"",""1"""\r\n'
).encode()
LEGIONOWO = (
    "﻿nazwa,cecha_ulicy,nazwa_ulicy,nr_budynku,nr_lokalu,kod_pocztowy,miejscowosc,"
    "kod_terc,kod_simc,szerokosc_geograficzna,dlugosc_geograficzna\r\n"
    "Urząd Miasta Legionowo,ulica,Piłsudskiego,41,,05-120,Legionowo,140801,0920806,"
    "52.395198,20.931382\r\n"
).encode()
WARSAW = json.dumps([{
    "geometry": {"coordinates": [[21.0148748, 52.2086170]], "type": "Point"},
    "properties": {
        "defibrillator_id": "622", "device_access_description": "Pn-Pt 8-16",
        "device_availability": "Ograniczona", "device_location": "Wewnątrz budynku",
        "device_manufacturer": "Medtronic", "device_public_access": "Publiczny",
        "location_building": "25/27", "location_city": "Warszawa",
        "location_description": "Przy wejściu na półpiętrze.",
        "location_object_name": "Urząd Dzielnicy Mokotów", "location_postcode": "02-517",
        "location_street": "Rakowiecka",
    },
}]).encode()
OSM = json.dumps({"type": "FeatureCollection", "features": [{
    "type": "Feature", "geometry": {"type": "Point", "coordinates": [21.01488, 52.20863]},
    "properties": {"@osm_id": 42, "@osm_type": "node", "emergency": "defibrillator",
                   "access": "customers", "indoor": "yes", "level": "1",
                   "opening_hours": "24/7", "operator": "Urząd Dzielnicy Mokotów",
                   "defibrillator:location:pl": "hol", "check_date": "2025-06-01"},
}]}).encode()

CTX = normalize.SourceContext(
    kind="dane_gov_pl", key="dgp1", name="Gmina", url="https://dane.gov.pl/pl/dataset/1",
    updated=date(2026, 1, 2),
)


# --- parsers ---------------------------------------------------------------------------


def test_parse_krosno_csv() -> None:
    rows = parsers.parse("csv", KROSNO)
    assert len(rows) == 1 and rows[0].props["Lokalizacja"] == "Zespół  Krytych Pływalni"


def test_parse_marki_row_wrapped_csv() -> None:
    rows = parsers.parse("csv", MARKI)
    assert len(rows) == 1
    assert rows[0].props["Adres"] == "Al.. Piłsudskiego 95, 05-270 Marki"


def test_parse_semicolon_csv() -> None:
    rows = parsers.parse("csv", "id;name;city\n744;AED ADM;Przemyśl\n".encode())
    assert rows[0].props == {"id": "744", "name": "AED ADM", "city": "Przemyśl"}


def test_parse_xlsx() -> None:
    wb = Workbook()
    wb.active.append(["nazwa", "szerokosc_geograficzna", "dlugosc_geograficzna"])
    wb.active.append(["Urząd", 52.1, 21.0])
    buf = io.BytesIO()
    wb.save(buf)
    rows = parsers.parse("xlsx", buf.getvalue())
    assert rows[0].props["nazwa"] == "Urząd" and rows[0].props["szerokosc_geograficzna"] == "52.1"


def test_parse_warsaw_nested_coordinates() -> None:
    row = parsers.parse("json", WARSAW)[0]
    assert (row.lon, row.lat) == (21.0148748, 52.2086170) and row.row_id == "622"


def test_parse_overpass() -> None:
    raw = json.dumps({"elements": [{"type": "way", "id": 7, "center": {"lat": 52, "lon": 21},
                                    "tags": {"access": "yes"}}]}).encode()
    row = parsers.parse("overpass-json", raw)[0]
    assert row.row_id == "way/7" and row.lat == 52


def test_unknown_format_raises() -> None:
    with pytest.raises(parsers.ParseError):
        parsers.parse("gml", b"<gml/>")


# --- normalization ---------------------------------------------------------------------


def test_parse_address() -> None:
    assert normalize.parse_address("ul. Stanisława Wyspiańskiego 20, 38-400 Krosno") == {
        "kod_pocztowy": "38-400", "miejscowosc": "Krosno", "cecha_ulicy": "ul.",
        "nazwa_ulicy": "Stanisława Wyspiańskiego", "nr_budynku": "20",
    }
    assert normalize.parse_address("Al.. Piłsudskiego 95, 05-270 Marki")["cecha_ulicy"] == "al."


def test_normalize_krosno_uses_place_name_not_generic() -> None:
    result = normalize.normalize_row(parsers.parse("csv", KROSNO)[0], CTX)
    assert result.valid and result.flags == []
    assert result.data["nazwa"] == "Zespół Krytych Pływalni"
    assert result.data["miejscowosc"] == "Krosno" and result.data["nazwa_ulicy"] == "Jasna"
    assert result.data["dostep"] == "nieznany"
    assert result.data["data_aktualizacji"] == "2026-01-02"
    assert result.data["id_aed"] == "dgp1-1"


def test_normalize_marki_swapped_coordinates() -> None:
    result = normalize.normalize_row(parsers.parse("csv", MARKI)[0], CTX)
    assert "wspolrzedne_zamienione" in result.flags
    assert (result.lat, result.lon) == (52.326697, 21.107557)


def test_normalize_legionowo_teryt() -> None:
    result = normalize.normalize_row(parsers.parse("csv", LEGIONOWO)[0], CTX)
    assert result.data["cecha_ulicy"] == "ul." and "cecha_ulicy_znormalizowana" in result.flags
    assert "kod_terc" not in result.data and "kod_terc_niepoprawny" in result.flags
    assert result.data["kod_simc"] == "0920806"


def test_normalize_warsaw_fields() -> None:
    result = normalize.normalize_row(parsers.parse("json", WARSAW)[0], CTX)
    d = result.data
    assert d["nazwa"] == "Urząd Dzielnicy Mokotów" and d["dostep"] == "publiczny"
    assert d["w_budynku"] is True and d["producent"] == "Medtronic"
    assert d["opis_lokalizacji"] == "Przy wejściu na półpiętrze."
    assert d["godziny_dostepnosci"] == "Pn-Pt 8-16" and "godziny_tekstem" in result.flags


def test_normalize_osm_tags() -> None:
    ctx = normalize.SourceContext("osm", "osm", "OpenStreetMap", "https://osm.org", None)
    d = normalize.normalize_row(parsers.parse("geojson", OSM)[0], ctx).data
    assert d["dostep"] == "ograniczony" and d["w_budynku"] is True and d["pietro"] == 1
    assert d["godziny_dostepnosci"] == "24/7" and d["opis_lokalizacji"] == "hol"
    assert d["data_aktualizacji"] == "2025-06-01"
    assert d["zrodlo_url"] == "https://www.openstreetmap.org/node/42"
    assert d["nazwa"] == "AED – Urząd Dzielnicy Mokotów"


def test_normalize_point_outside_poland_invalid() -> None:
    row = parsers.RawRow("1", {"nazwa": "X", "lat": "48.1", "lon": "11.5"})
    result = normalize.normalize_row(row, CTX)
    assert not result.valid and "wspolrzedne_poza_polska" in result.flags


def test_coverage_ignores_unknown() -> None:
    cov = normalize.coverage([{"nazwa": "A", "dostep": "nieznany"}, {"nazwa": "B"}])
    assert cov["fields"]["nazwa"] == 1.0 and cov["fields"]["dostep"] == 0.0


# --- merge -----------------------------------------------------------------------------


def _resource(kind: str, ext: str, fmt: str, raw: bytes) -> SourceResource:
    ds = SourceDataset.objects.create(kind=kind, external_id=ext, title=f"ds {ext}",
                                      publisher=f"pub {ext}")
    return SourceResource.objects.create(dataset=ds, external_id="r", format=fmt,
                                         url=f"https://x.test/{ext}", raw=raw,
                                         fetch_status="ok", selected=True)


@pytest.mark.django_db
def test_merge_warsaw_and_osm_into_one_aed_official_first() -> None:
    _resource("dane_gov_pl", "39512", "json", WARSAW)
    _resource("osm", "openaedmap-pl", "geojson", OSM)
    summary = merge.process_all()
    assert summary["aeds"] == 1 and summary["merged_groups"] == 1
    aed = AED.objects.get()
    assert aed.sources_count == 2
    assert aed.data["nazwa"] == "Urząd Dzielnicy Mokotów"  # official name wins
    assert aed.data["dostep"] == "publiczny"  # official value wins over OSM
    assert aed.data["pietro"] == 1  # filled from OSM
    assert aed.data["zrodlo"] == "pub 39512; OpenStreetMap"
    assert aed.id_aed.startswith("PL-AED-")


@pytest.mark.django_db
def test_same_resource_records_never_merged_even_via_chain() -> None:
    two_devices = json.dumps([
        {"geometry": {"coordinates": [[21.0, 52.0]]}, "properties": {"defibrillator_id": "1",
         "location_object_name": "Szkoła"}},
        {"geometry": {"coordinates": [[21.0, 52.0]]}, "properties": {"defibrillator_id": "2",
         "location_object_name": "Szkoła"}},
    ]).encode()
    between = json.dumps({"features": [{"geometry": {"type": "Point",
                                                     "coordinates": [21.00005, 52.0]},
                                        "properties": {"@osm_id": 1}}]}).encode()
    _resource("dane_gov_pl", "1", "json", two_devices)
    _resource("osm", "openaedmap-pl", "geojson", between)
    merge.process_all()
    assert AED.objects.count() == 2
    for aed in AED.objects.all():
        ids = list(aed.source_records.values_list("resource_id", flat=True))
        assert len(ids) == len(set(ids))


@pytest.mark.django_db
def test_far_points_not_merged_and_outlier_flagged() -> None:
    rows = [{"geometry": {"coordinates": [[21.0 + i * 0.01, 52.0]]},
             "properties": {"defibrillator_id": str(i), "location_object_name": f"A{i}"}}
            for i in range(3)]
    rows.append({"geometry": {"coordinates": [[21.72, 49.71]]},  # copied from another city
                 "properties": {"defibrillator_id": "99", "location_object_name": "Kopia"}})
    _resource("dane_gov_pl", "2", "json", json.dumps(rows).encode())
    merge.process_all()
    outlier = SourceRecord.objects.get(source_row_id="99")
    assert not outlier.valid and "wspolrzedne_daleko_od_pozostalych" in outlier.quality_flags
    assert AED.objects.count() == 3


@pytest.mark.django_db
def test_parse_error_recorded() -> None:
    res = _resource("dane_gov_pl", "3", "json", b"not json")
    merge.process_all()
    res.refresh_from_db()
    assert res.parse_status == "error" and res.record_count == 0


@pytest.mark.django_db
def test_sources_report_endpoint() -> None:
    _resource("dane_gov_pl", "39512", "json", WARSAW)
    _resource("osm", "openaedmap-pl", "geojson", OSM)
    blocked = SourceDataset.objects.create(kind="dane_gov_pl", external_id="9", title="Blocked")
    SourceResource.objects.create(dataset=blocked, external_id="b", url="https://b.test",
                                  fetch_status="requires_api_key", fetch_error="needs token")
    merge.process_all()
    body = APIClient().get("/api/sources/").json()
    assert body["aed_count"] == 1 and body["multi_source_aed_count"] == 1
    by_id = {s["id"]: s for s in body["sources"]}
    warsaw = by_id["dane_gov_pl:39512"]
    assert warsaw["status"] == "ok" and warsaw["record_count"] == 1
    assert warsaw["confirmed_by_other_sources"] == 1
    assert warsaw["coverage"]["fields"]["opis_lokalizacji"] == 1.0
    assert by_id["dane_gov_pl:9"]["status"] == "requires_api_key"
    assert by_id["dane_gov_pl:9"]["coverage"] is None

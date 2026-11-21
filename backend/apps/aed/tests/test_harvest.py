"""Tests for the AED harvester (T02) — no network, a fake HTTP client serves fixtures."""

import json

import pytest

from apps.aed import harvest
from apps.aed.models import SourceDataset, SourceResource

API = harvest.DANE_API_URL


def _json(payload: dict) -> harvest.HttpResponse:
    return harvest.HttpResponse(json.dumps(payload).encode(), "application/json")


def _search_page(items: list[dict]) -> dict:
    return {"data": items, "links": {}}


def _search_item(item_id: str, model: str, title: str, dataset_id: str | None = None) -> dict:
    item = {"id": item_id, "type": "common", "attributes": {"model": model, "title": title}}
    if dataset_id:
        item["relationships"] = {"dataset": {"data": {"id": dataset_id, "type": "dataset"}}}
    return item


KROSNO_CSV = (
    "Długość geograficzna,Szerokość geograficzna, Nazwa, Lokalizacja, Adres, Numer Id\n"
    '21.72,49.71,"Defibrylator","Zespół Krytych Pływalni","ul. Jasna, 38-400 Krosno","1"\n'
).encode()
GEOJSON = json.dumps(
    {"type": "FeatureCollection", "features": [
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [22.7, 49.78]},
         "properties": {"name": "AED"}}]}
).encode()


class FakeClient(harvest.HttpClient):
    """Serves canned responses; unknown URLs raise ConnectionError (like a dead host)."""

    def __init__(self, routes: dict[str, harvest.HttpResponse]):
        super().__init__(retries=1, backoff=0)
        self.routes = routes
        self.calls: list[str] = []

    def request(
        self, url: str, data: bytes | None = None, headers: dict | None = None
    ) -> harvest.HttpResponse:
        self.calls.append(url)
        self.headers = headers or {}
        for prefix, response in self.routes.items():
            if url == prefix or (prefix.endswith("*") and url.startswith(prefix[:-1])):
                if isinstance(response, Exception):
                    raise response
                return response
        raise ConnectionError(f"no route for {url}")


def _routes() -> dict[str, harvest.HttpResponse]:
    search = _search_page([
        _search_item("54632", "resource", "<mark>Defibrylatory</mark> w Krośnie", "3624"),
        _search_item("4581", "dataset", "Lokalizacje AED w Przemyślu"),
        _search_item("2625221", "resource", "Wykaz defibrylatorów AED w Legionowie", "40593"),
        _search_item("31843", "dataset", "Baza pojazdów ZTM w Gdańsku"),  # irrelevant hit
    ])
    return {
        f"{API}/search*": _json(search),
        f"{API}/datasets/3624": _json({"data": {"id": "3624", "attributes": {
            "title": "Defibrylatory zlokalizowane w Mieście Krosno", "license_name": "CC0 1.0",
            "modified": "2024-02-19T10:00:00Z"},
            "relationships": {"institution": {"data": {"id": "11"}}}}}),
        f"{API}/datasets/3624/resources?per_page=100": _json({"data": [
            {"id": "54632", "attributes": {"title": "Defibrylatory Krosno", "format": "CSV",
                                           "file_url": "https://files.test/krosno.csv"}}]}),
        f"{API}/institutions/11": _json({"data": {"attributes": {"title": "Miasto Krosno"}}}),
        f"{API}/datasets/4581": _json({"data": {"id": "4581", "attributes": {
            "title": "Lokalizacje AED w Przemyślu", "license_name": "CC BY 4.0"},
            "relationships": {}}}),
        f"{API}/datasets/4581/resources?per_page=100": _json({"data": [
            {"id": "62095", "attributes": {"title": "AED csv", "format": "csv",
                                           "link": "https://przemysl.test/csv"}},
            {"id": "62093", "attributes": {"title": "AED geojson", "format": "geojson",
                                           "link": "https://przemysl.test/geojson"}},
            {"id": "62092", "attributes": {"title": "AED gml", "format": "xml",
                                           "link": "https://przemysl.test/gml"}},
            {"id": "62424", "attributes": {"title": "AED gml copy", "format": "xml",
                                           "link": "https://przemysl.test/gml"}},
            {"id": "62500", "attributes": {"title": "AED gml re-upload", "format": "xml",
                                           "link": "https://przemysl.test/gml-2024-11"}},
        ]}),
        f"{API}/datasets/40593": _json({"data": {"id": "40593", "attributes": {
            "title": "Zdrowie", "license_name": "CC0 1.0"}, "relationships": {}}}),
        f"{API}/datasets/40593/resources?per_page=100": _json({"data": [
            {"id": "2631129", "attributes": {"title": "Wykaz aptek w Legionowie", "format": "csv",
                                             "file_url": "https://files.test/apteki.csv"}},
            {"id": "2625221", "attributes": {"title": "Wykaz defibrylatorów AED", "format": "csv",
                                             "file_url": "https://files.test/aed.csv"}},
        ]}),
        "https://files.test/krosno.csv": harvest.HttpResponse(KROSNO_CSV, "text/csv"),
        "https://files.test/aed.csv": harvest.HttpResponse(KROSNO_CSV, "text/csv"),
        "https://przemysl.test/csv": harvest.HttpResponse(b"id;name\n1;AED", "text/csv"),
        "https://przemysl.test/geojson": harvest.HttpResponse(GEOJSON, "application/geo+json"),
        "https://przemysl.test/gml": harvest.HttpResponse(b"<gml/>", "application/xml"),
        "https://przemysl.test/gml-2024-11": harvest.HttpResponse(b"<gml/>", "application/xml"),
        harvest.OSM_PRIMARY_URL: harvest.HttpResponse(GEOJSON, "application/geo+json"),
    }


def test_discover_filters_irrelevant_and_resolves_resource_hits() -> None:
    ids = harvest.discover_dane_dataset_ids(FakeClient(_routes()))
    assert ids == ["3624", "4581", "40593"]


@pytest.mark.django_db
def test_harvest_all_stores_datasets_resources_and_selects_best_format() -> None:
    report = harvest.harvest_all(FakeClient(_routes()))

    assert report.errors == []
    assert SourceDataset.objects.filter(kind="dane_gov_pl").count() == 3
    assert SourceDataset.objects.filter(kind="osm").count() == 1
    krosno = SourceDataset.objects.get(external_id="3624")
    assert krosno.publisher == "Miasto Krosno"
    assert krosno.url == "https://dane.gov.pl/pl/dataset/3624"

    przemysl = SourceDataset.objects.get(external_id="4581")
    selected = przemysl.resources.get(selected=True)
    assert selected.format == "geojson"  # GeoJSON preferred over CSV/XML
    dup = przemysl.resources.get(external_id="62424")
    assert dup.fetch_status == SourceResource.FetchStatus.DUPLICATE
    same_content = przemysl.resources.get(external_id="62500")
    assert same_content.fetch_status == SourceResource.FetchStatus.DUPLICATE
    assert "Same content" in same_content.fetch_error

    # Mixed dataset "Zdrowie": pharmacies resource skipped, AED resource kept.
    legionowo = SourceDataset.objects.get(external_id="40593")
    assert list(legionowo.resources.values_list("external_id", flat=True)) == ["2625221"]

    osm = SourceResource.objects.get(dataset__kind="osm")
    assert osm.selected and bytes(osm.raw) == GEOJSON


@pytest.mark.django_db
def test_harvest_is_idempotent() -> None:
    harvest.harvest_all(FakeClient(_routes()))
    harvest.harvest_all(FakeClient(_routes()))
    assert SourceDataset.objects.count() == 4
    assert SourceResource.objects.count() == 1 + 5 + 1 + 1


@pytest.mark.django_db
def test_failed_download_is_recorded_not_raised() -> None:
    routes = _routes()
    del routes["https://files.test/krosno.csv"]
    harvest.harvest_all(FakeClient(routes))
    res = SourceResource.objects.get(external_id="54632")
    assert res.fetch_status == SourceResource.FetchStatus.ERROR
    assert "no route" in res.fetch_error
    assert not res.selected


@pytest.mark.django_db
def test_html_link_marked_not_machine_readable() -> None:
    routes = _routes()
    routes["https://files.test/krosno.csv"] = harvest.HttpResponse(
        b"<!DOCTYPE html><html>catalogue</html>", "text/html; charset=utf-8"
    )
    harvest.harvest_all(FakeClient(routes))
    res = SourceResource.objects.get(external_id="54632")
    assert res.fetch_status == SourceResource.FetchStatus.NOT_MACHINE_READABLE
    assert res.raw is None


@pytest.mark.django_db
def test_osm_falls_back_to_overpass() -> None:
    routes = _routes()
    del routes[harvest.OSM_PRIMARY_URL]
    overpass = json.dumps({"elements": [{"type": "node", "id": 1, "lat": 52.0, "lon": 21.0,
                                         "tags": {"emergency": "defibrillator"}}]}).encode()
    routes[harvest.OVERPASS_URLS[0]] = harvest.HttpResponse(overpass, "application/json")
    harvest.harvest_all(FakeClient(routes))
    osm = SourceResource.objects.get(dataset__kind="osm")
    assert osm.format == "overpass-json" and osm.selected


@pytest.mark.django_db
def test_search_failure_reported() -> None:
    report = harvest.harvest_all(FakeClient({}), include_osm=False)
    assert report.errors and "search failed" in report.errors[0]


@pytest.mark.django_db
def test_snapshot_roundtrip(tmp_path) -> None:
    harvest.harvest_all(FakeClient(_routes()))
    assert harvest.save_snapshot(tmp_path) == 4
    SourceResource.objects.all().delete()
    SourceDataset.objects.all().delete()

    report = harvest.load_snapshot(tmp_path)
    assert len(report.datasets) == 4
    assert SourceResource.objects.get(dataset__kind="osm").selected
    assert bytes(SourceResource.objects.get(external_id="54632").raw) == KROSNO_CSV


WARSAW_UUID = "7bc32ffc-c2ac-4d32-83c9-b6f7a0b38de8"
WARSAW_DATA = json.dumps([{
    "geometry": {"coordinates": [[21.0148, 52.2086]], "type": "Point"},
    "properties": {"defibrillator_id": "622", "location_city": "Warszawa"},
}]).encode()


def _warsaw_routes() -> dict:
    routes = _routes()
    routes[f"{API}/search*"] = _json(_search_page([
        _search_item("2512040", "resource", "Lokalizacja defibrylatorów (AED)", "39512")]))
    routes[f"{API}/datasets/39512"] = _json({"data": {"id": "39512", "attributes": {
        "title": "Lokalizacja defibrylatorów (AED)"}, "relationships": {}}})
    routes[f"{API}/datasets/39512/resources?per_page=100"] = _json({"data": [
        {"id": "2512040", "attributes": {
            "title": "Lokalizacja defibrylatorów (AED)", "format": "json",
            "link": f"https://dane.um.warszawa.pl/pl/catalogue/{WARSAW_UUID}"}}]})
    routes[harvest.WARSAW_META_URL.format(uuid=WARSAW_UUID)] = _json(
        {"call_examples": "https://dane.um.warszawa.pl/files/aed_pw.json"})
    routes["https://dane.um.warszawa.pl/files/aed_pw.json"] = harvest.HttpResponse(
        b"curl --request POST 'https://dane.um.warszawa.pl/api/action/get_aed_test' "
        b"--header 'Authorization: token_uzytkownika'", "application/json")
    return routes


@pytest.mark.django_db
def test_warsaw_without_token_reports_requires_api_key(settings) -> None:
    settings.WARSAW_API_TOKEN = ""
    harvest.harvest_all(FakeClient(_warsaw_routes()), include_osm=False)
    res = SourceResource.objects.get(external_id="2512040")
    assert res.fetch_status == SourceResource.FetchStatus.REQUIRES_API_KEY
    assert "get_aed_test" in res.fetch_error and "WARSAW_API_TOKEN" in res.fetch_error


@pytest.mark.django_db
def test_warsaw_with_token_fetches_api_and_sends_header(settings) -> None:
    settings.WARSAW_API_TOKEN = "secret-token"
    routes = _warsaw_routes()
    routes["https://dane.um.warszawa.pl/api/action/get_aed_test"] = harvest.HttpResponse(
        WARSAW_DATA, "application/json")
    client = FakeClient(routes)
    harvest.harvest_all(client, include_osm=False)
    res = SourceResource.objects.get(external_id="2512040")
    assert res.fetch_status == SourceResource.FetchStatus.OK
    assert bytes(res.raw) == WARSAW_DATA and res.selected
    assert client.headers.get("Authorization") == "secret-token"
    assert "secret-token" not in res.fetch_error  # token never stored


@pytest.mark.django_db
def test_warsaw_rejected_token(settings) -> None:
    settings.WARSAW_API_TOKEN = "bad"
    routes = _warsaw_routes()
    routes["https://dane.um.warszawa.pl/api/action/get_aed_test"] = PermissionError("HTTP 403")
    harvest.harvest_all(FakeClient(routes), include_osm=False)
    res = SourceResource.objects.get(external_id="2512040")
    assert res.fetch_status == SourceResource.FetchStatus.REQUIRES_API_KEY
    assert "rejected" in res.fetch_error

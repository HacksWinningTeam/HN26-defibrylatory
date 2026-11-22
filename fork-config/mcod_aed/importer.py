"""Mirror the AED datasets of dane.gov.pl (+ OpenStreetMap) into this portal as separate datasets
of their own institutions, all with "Standard danych" = aed-pl (T12, DEC-014/015).

* Discovery: public search of api.dane.gov.pl/1.4 (same rules as the original harvester).
* Per dataset the best AED resource is mirrored (geojson > csv > xlsx > json > xml); downloadable
  files are uploaded as files, the Warsaw catalogue entry becomes a connected API (city API + token).
* OpenStreetMap (OpenAEDMap export for Poland) is a connected API resource.
* `offline=True` (or dane.gov.pl unreachable) uses the committed snapshot in fixtures/snapshot/.
"""
import json
import logging
import os
import re
import urllib.parse
from dataclasses import dataclass, field

import requests

from mcod.aed import connectors, publishing

logger = logging.getLogger("mcod")

DANE_API_URL = "https://api.dane.gov.pl/1.4"
DANE_PORTAL_URL = "https://dane.gov.pl/pl/dataset"
SEARCH_QUERIES = ("defibrylator", "defibrylatory", "defibrylatorów", "AED")
AED_TITLE_RE = re.compile(r"defibryl|defibryz|\bAED\b", re.IGNORECASE)
FORMAT_PRIORITY = ("geojson", "csv", "xlsx", "xls", "json", "xml", "gml")
WARSAW_CATALOGUE_RE = re.compile(r"dane\.um\.warszawa\.pl/(?:pl/)?catalogue/", re.IGNORECASE)
SNAPSHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "snapshot")
TIMEOUT = 60
OSM_EXT_IDENT = "osm-openaedmap-pl"
CORRECTED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "corrected")
# Sources whose original file fails the standard: the original stays (blocked by validation) and a
# corrected copy is published next to it, so both are visible in the portal (user decision, T12).
CORRECTED_FILES = {
    "40593": dict(
        file="aed-40593-legionowo-poprawiony.csv",
        title="Wykaz defibrylatorów AED w Legionowie – wersja poprawiona (zgodna ze standardem AED)",
        description=(
            "Poprawiona kopia pliku Urzędu Miasta Legionowo: cecha ulicy zgodnie ze słownikiem standardu "
            "(„ulica” → „ul.”, „aleja” → „al.”) oraz 7-cyfrowy kod TERC gminy (140801 → 1408011). "
            "Oryginał pozostaje w zbiorze jako szkic zablokowany przez walidację."
        ),
    ),
}
INSTITUTION_TYPES = {"urząd": "local", "gmina": "local", "miasto": "local", "starostwo": "local"}


@dataclass
class SourceDatasetSpec:
    dane_id: str
    title: str
    notes: str
    publisher: str
    license_name: str
    frequency: str
    resource_id: str = ""
    resource_title: str = ""
    resource_format: str = ""
    file_url: str = ""
    content: bytes = b""
    api_link: str = ""


@dataclass
class ImportReport:
    mode: str = "online"
    rows: list = field(default_factory=list)  # (institution, dataset, resource kind, action)
    errors: list = field(default_factory=list)


def _get_json(url):
    resp = requests.get(url, timeout=TIMEOUT, headers={"User-Agent": "dane.gov.pl mcod.aed importer"})
    resp.raise_for_status()
    return resp.json()


def _strip_html(text):
    return re.sub(r"<[^>]+>", "", text or "")


def discover_dataset_ids():
    found = {}
    for query in SEARCH_QUERIES:
        url = "{}/search?{}".format(DANE_API_URL, urllib.parse.urlencode({"q": query, "per_page": 100}))
        for _ in range(5):
            payload = _get_json(url)
            for item in payload.get("data", []):
                attrs = item.get("attributes", {})
                if not AED_TITLE_RE.search(_strip_html(attrs.get("title"))):
                    continue
                if attrs.get("model") == "dataset":
                    found[str(item["id"])] = None
                elif attrs.get("model") == "resource":
                    rel = item.get("relationships", {}).get("dataset", {}).get("data") or {}
                    if rel.get("id"):
                        found[str(rel["id"])] = None
            url = payload.get("links", {}).get("next")
            if not url:
                break
    return list(found)


def _rank(fmt):
    fmt = (fmt or "").lower()
    return FORMAT_PRIORITY.index(fmt) if fmt in FORMAT_PRIORITY else len(FORMAT_PRIORITY)


def fetch_dataset_spec(dane_id, institutions):
    payload = _get_json("{}/datasets/{}".format(DANE_API_URL, dane_id))["data"]
    attrs = payload["attributes"]
    inst_id = ((payload.get("relationships", {}).get("institution") or {}).get("data") or {}).get("id")
    if inst_id and inst_id not in institutions:
        try:
            institutions[inst_id] = _get_json("{}/institutions/{}".format(DANE_API_URL, inst_id))["data"]["attributes"]["title"]
        except (requests.RequestException, KeyError, ValueError):
            institutions[inst_id] = ""
    spec = SourceDatasetSpec(
        dane_id=str(dane_id), title=_strip_html(attrs.get("title")).strip(), notes=attrs.get("notes") or "",
        publisher=institutions.get(inst_id) or "Instytucja {}".format(inst_id),
        license_name=attrs.get("license_name") or "", frequency=attrs.get("update_frequency") or "",
    )
    dataset_is_aed = bool(AED_TITLE_RE.search(spec.title))
    resources = _get_json("{}/datasets/{}/resources?per_page=100".format(DANE_API_URL, dane_id)).get("data", [])
    candidates = []
    for item in resources:
        r_attrs = item["attributes"]
        title = _strip_html(r_attrs.get("title"))
        if not dataset_is_aed and not AED_TITLE_RE.search(title):
            continue  # mixed datasets (Legionowo "Zdrowie": pharmacies + AEDs)
        url = r_attrs.get("file_url") or r_attrs.get("link") or ""
        if url:
            candidates.append((_rank(r_attrs.get("format")), str(item["id"]), title, (r_attrs.get("format") or "").lower(), url))
    if not candidates:
        return spec
    _, spec.resource_id, spec.resource_title, spec.resource_format, url = sorted(candidates)[0]
    if WARSAW_CATALOGUE_RE.search(url):
        spec.api_link = connectors.WARSAW_AED_ACTION
        spec.resource_format = "json"
    else:
        spec.file_url = url
        spec.content, _ = connectors.fetch_url(url)
    return spec


def snapshot_specs():
    with open(os.path.join(SNAPSHOT_DIR, "manifest.json"), encoding="utf-8") as fh:
        manifest = json.load(fh)
    specs = []
    for ds in manifest["datasets"]:
        selected = [r for r in ds["resources"] if r.get("selected")] or ds["resources"][:1]
        if not selected:
            continue
        res = selected[0]
        spec = SourceDatasetSpec(
            dane_id=ds["external_id"], title=ds["title"], notes="", publisher=ds["publisher"],
            license_name=ds.get("license_name") or "", frequency="", resource_id=res["external_id"],
            resource_title=res["title"], resource_format=res["format"], file_url=res["url"],
        )
        if WARSAW_CATALOGUE_RE.search(res["url"]) or ds["external_id"] == "39512":
            spec.api_link = connectors.WARSAW_AED_ACTION
            spec.resource_format = "json"
        else:
            with open(os.path.join(SNAPSHOT_DIR, res["file"]), "rb") as fh:
                spec.content = fh.read()
        specs.append(spec)
    return specs


def _institution_type(name):
    lowered = name.lower()
    for key, value in INSTITUTION_TYPES.items():
        if key in lowered:
            return value
    return "state"


def _notes(spec, standard=None):
    source = "{}/{}".format(DANE_PORTAL_URL, spec.dane_id)
    if standard is not None and standard.code != "aed-pl":
        body = spec.notes.strip() or "<p>{}</p>".format(spec.title)
        if not body.startswith("<"):
            body = "<p>{}</p>".format(body)
        target = (standard.publish or {}).get("title", "zbioru zbiorczego")
        return body + ("<p>Zbiór źródłowy z dane.gov.pl: <a href=\"{0}\">{0}</a>. Należy do standardu danych "
                       "„{1}” – jego dane są walidowane ze wzorcowym zakresem i agregowane do zbioru „{2}”.</p>"
                       ).format(source, standard.name, target)
    body = spec.notes.strip() or "<p>{}</p>".format(spec.title)
    if not body.startswith("<"):
        body = "<p>{}</p>".format(body)
    return body + (
        "<p>Zbiór źródłowy z dane.gov.pl: <a href=\"{0}\">{0}</a>. Należy do standardu danych "
        "„Dane AED” – jego dane są walidowane ze wzorcowym zakresem i agregowane do zbioru "
        "„Defibrylatory AED – zbiór ogólnopolski”.</p>"
    ).format(source)


def import_spec(spec, standard, report, force=False, category_code="HEAL", tags=("AED", "defibrylatory", "zdrowie")):
    org, _ = publishing.ensure_organization(spec.publisher, institution_type=_institution_type(spec.publisher))
    ds, ds_action = publishing.ensure_dataset(
        org, spec.title, "dgp-{}".format(spec.dane_id), _notes(spec, standard), standard=standard,
        license_name=spec.license_name, update_frequency=publishing.frequency_code(spec.frequency),
        url="{}/{}".format(DANE_PORTAL_URL, spec.dane_id), category_code=category_code, tags=tags,
    )
    ext = "dgp-res-{}".format(spec.resource_id or spec.dane_id)
    description = "Kopia zasobu z dane.gov.pl ({}). Format oryginalny: {}.".format(
        spec.file_url or "{}/{}".format(DANE_PORTAL_URL, spec.dane_id), (spec.resource_format or "?").upper())
    if spec.api_link:
        res, action = publishing.ensure_api_resource(
            ds, ext, spec.resource_title or spec.title,
            "Połączone API m.st. Warszawy (dane.um.warszawa.pl, wymaga bezpłatnego tokenu). "
            "Zbiór na dane.gov.pl wskazuje tylko stronę katalogu; dane pobierane są na żywo z API.",
            spec.api_link,
        )
        kind = "API"
    else:
        if not spec.content:
            report.errors.append("{}: brak pliku do zaimportowania".format(spec.title))
            return
        ext_name = spec.resource_format if spec.resource_format not in ("", "gml") else "xml"
        res, action = publishing.ensure_file_resource(
            ds, ext, spec.resource_title or spec.title, description,
            "aed-{}.{}".format(spec.dane_id, ext_name), spec.content, fmt=ext_name, force=force,
        )
        kind = "plik {}".format(ext_name.upper())
    report.rows.append((org.title, ds.id, ds.title, res.id, kind, "{} / {}".format(ds_action, action)))
    corrected = CORRECTED_FILES.get(spec.dane_id)
    if corrected:
        with open(os.path.join(CORRECTED_DIR, corrected["file"]), "rb") as fh:
            content = fh.read()
        fixed, fixed_action = publishing.ensure_file_resource(
            ds, ext + "-fix", corrected["title"], corrected["description"], corrected["file"], content,
            fmt="csv", position=2, force=force,
        )
        report.rows.append((org.title, ds.id, ds.title, fixed.id, "plik CSV (poprawiony)", fixed_action))


def import_osm(standard, report):
    org, _ = publishing.ensure_organization(
        "Współtwórcy OpenStreetMap (OpenAEDMap)", institution_type="other", website="https://openaedmap.org/")
    ds, ds_action = publishing.ensure_dataset(
        org, "OpenStreetMap – defibrylatory AED w Polsce", OSM_EXT_IDENT,
        "<p>Defibrylatory AED w Polsce z OpenStreetMap (tag emergency=defibrillator), codzienny eksport "
        "OpenAEDMap. Połączone API – dane pobierane na żywo.</p>",
        standard=standard, license_name="CC BY-SA 4.0",
        license_text="Dane OpenStreetMap: © współtwórcy OpenStreetMap, licencja Open Database License (ODbL 1.0) "
                     "https://opendatacommons.org/licenses/odbl/1-0/ – wymagane uznanie autorstwa i udostępnianie "
                     "baz pochodnych na tej samej licencji.",
        update_frequency="daily", url="https://openaedmap.org/",
    )
    res, action = publishing.ensure_api_resource(
        ds, "osm-openaedmap-pl-geojson", "OpenAEDMap – AED w Polsce (GeoJSON, API)",
        "Połączone API: eksport GeoJSON OpenAEDMap dla Polski ({}).".format(connectors.OSM_AED_URL),
        connectors.OSM_AED_URL,
    )
    report.rows.append((org.title, ds.id, ds.title, res.id, "API", "{} / {}".format(ds_action, action)))


def run_import(offline=False, include_osm=True, force=False):
    from mcod.aed.standards import AED_STANDARD_CODE, ensure_aed_standard
    from mcod.aed.models import DataStandard

    standard = DataStandard.objects.filter(code=AED_STANDARD_CODE).first() or ensure_aed_standard()
    report = ImportReport(mode="offline" if offline else "online")
    specs = None
    if not offline:
        try:
            institutions = {}
            specs = [fetch_dataset_spec(dane_id, institutions) for dane_id in discover_dataset_ids()]
        except (requests.RequestException, connectors.SourceLoadError, ValueError, KeyError) as exc:
            report.errors.append("dane.gov.pl niedostępne ({}), użyto kopii offline".format(exc))
            report.mode = "offline (fallback)"
    if specs is None:
        specs = snapshot_specs()
    for spec in specs:
        try:
            import_spec(spec, standard, report, force=force)
        except Exception as exc:  # keep importing the other sources
            logger.exception("mcod.aed import of %s failed", spec.dane_id)
            report.errors.append("{}: {}".format(spec.title, exc))
    if include_osm:
        try:
            import_osm(standard, report)
        except Exception as exc:
            logger.exception("mcod.aed OSM import failed")
            report.errors.append("OpenStreetMap: {}".format(exc))
    return report


# --- Data-defined standards (T18, DEC-019) ------------------------------------------------------

KNOWN_FORMATS = ("csv", "xlsx", "xls", "json", "geojson", "xml")
GENERIC_PRIORITY = ("csv", "xlsx", "xls", "geojson", "json", "xml")


def effective_format(declared, url):
    """The file extension wins over the declared format (dane.gov.pl labels some CSV/RDF files 'xlsx')."""
    path = (url or "").split("?", 1)[0].lower()
    ext = path.rsplit(".", 1)[-1] if "." in path.rsplit("/", 1)[-1] else ""
    if ext in KNOWN_FORMATS or ext in ("rdf", "ttl", "pdf", "doc", "docx", "html", "htm", "zip"):
        return ext
    return (declared or "").lower()


def discover_for_standard(discovery):
    title_re = re.compile(discovery.get("title_pattern", "."), re.IGNORECASE)
    exclude = discovery.get("exclude_pattern")
    exclude_re = re.compile(exclude, re.IGNORECASE) if exclude else None
    found = {}
    for query in discovery.get("queries", []):
        url = "{}/datasets?{}".format(DANE_API_URL, urllib.parse.urlencode({"q": query, "per_page": 100}))
        for _ in range(3):
            payload = _get_json(url)
            for item in payload.get("data", []):
                title = _strip_html(item.get("attributes", {}).get("title"))
                if title_re.search(title) and not (exclude_re and exclude_re.search(title)):
                    found[str(item["id"])] = title
            url = payload.get("links", {}).get("next")
            if not url:
                break
    return found


def fetch_generic_spec(dane_id, institutions):
    """Dataset metadata + its best tabular resource (by real file extension). None if nothing usable."""
    payload = _get_json("{}/datasets/{}".format(DANE_API_URL, dane_id))["data"]
    attrs = payload["attributes"]
    inst_id = ((payload.get("relationships", {}).get("institution") or {}).get("data") or {}).get("id")
    if inst_id and inst_id not in institutions:
        try:
            institutions[inst_id] = _get_json("{}/institutions/{}".format(DANE_API_URL, inst_id))["data"]["attributes"]["title"]
        except (requests.RequestException, KeyError, ValueError):
            institutions[inst_id] = ""
    spec = SourceDatasetSpec(
        dane_id=str(dane_id), title=_strip_html(attrs.get("title")).strip(), notes=attrs.get("notes") or "",
        publisher=institutions.get(inst_id) or "Instytucja {}".format(inst_id),
        license_name=attrs.get("license_name") or "", frequency=attrs.get("update_frequency") or "",
    )
    candidates = []
    for item in _get_json("{}/datasets/{}/resources?per_page=50".format(DANE_API_URL, dane_id)).get("data", []):
        r_attrs = item["attributes"]
        url = r_attrs.get("file_url") or r_attrs.get("link") or ""
        fmt = effective_format(r_attrs.get("format"), url)
        if url and fmt in GENERIC_PRIORITY:
            candidates.append((GENERIC_PRIORITY.index(fmt), str(item["id"]), _strip_html(r_attrs.get("title")), fmt, url))
    if not candidates:
        return None
    _, spec.resource_id, spec.resource_title, spec.resource_format, spec.file_url = sorted(candidates)[0]
    spec.content, _ = connectors.fetch_url(spec.file_url)
    return spec


def run_generic_import(standard, force=False):
    """Mirror the datasets matching `standard.discovery` (max `max_datasets` with usable data)."""
    from mcod.aed import validation

    discovery = standard.discovery or {}
    report = ImportReport(mode="online")
    publish = standard.publish or {}
    tags = tuple(publish.get("tags") or (standard.name,))
    category = publish.get("category", "SOCI")
    limit = int(discovery.get("max_datasets", 8))
    institutions, imported = {}, 0
    try:
        found = discover_for_standard(discovery)
    except (requests.RequestException, ValueError, KeyError) as exc:
        report.errors.append("dane.gov.pl niedostępne: {}".format(exc))
        return report
    for dane_id, title in found.items():
        if imported >= limit:
            break
        try:
            spec = fetch_generic_spec(dane_id, institutions)
            if spec is None:
                report.errors.append("{} {}: brak zasobu w formacie tabelarycznym – pominięto".format(dane_id, title))
                continue
            validation.parse_bytes(spec.content, filename=spec.file_url.rsplit("/", 1)[-1], fmt=spec.resource_format)
            import_spec(spec, standard, report, force=force, category_code=category, tags=tags)
            imported += 1
        except validation.ValidationInputError as exc:
            report.errors.append("{} {}: plik nieczytelny ({}) – pominięto".format(dane_id, title, str(exc)[:80]))
        except Exception as exc:  # keep importing the other sources
            logger.exception("mcod.aed generic import of %s failed", dane_id)
            report.errors.append("{} {}: {}".format(dane_id, title, str(exc)[:120]))
    return report

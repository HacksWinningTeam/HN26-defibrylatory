"""Harvest AED sources: every AED dataset on dane.gov.pl + OpenStreetMap AEDs in Poland (T02).

The HTTP layer is a tiny injectable client so tests run without network access.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.aed.models import SourceDataset, SourceResource

logger = logging.getLogger(__name__)

DANE_API_URL = "https://api.dane.gov.pl/1.4"
DANE_PORTAL_URL = "https://dane.gov.pl/pl/dataset"
SEARCH_QUERIES = ("defibrylator", "defibrylatory", "defibrylatorów", "AED")
SEARCH_MAX_PAGES = 5
AED_TITLE_RE = re.compile(r"defibryl|defibryz|\bAED\b", re.IGNORECASE)

# OpenAEDMap publishes a daily GeoJSON of all OSM `emergency=defibrillator` objects per country.
OSM_PRIMARY_URL = "https://openaedmap.org/api/v1/countries/PL.geojson"
OVERPASS_URLS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
)
OVERPASS_QUERY = (
    '[out:json][timeout:120];area["ISO3166-1"="PL"][admin_level=2]->.pl;'
    'nwr["emergency"="defibrillator"](area.pl);out center tags;'
)
OSM_DATASET_ID = "openaedmap-pl"

TIMEOUT = 60
RETRIES = 3
USER_AGENT = "aed-pl-harvester/1.0 (open data prototype)"

# Preferred format when a dataset publishes the same data several times.
FORMAT_PRIORITY = ("geojson", "csv", "xlsx", "xls", "json", "xml", "gml")
HTML_TYPES = ("text/html", "application/xhtml")

# Warsaw: dane.gov.pl links to a catalogue page; the data is behind a token-protected API.
WARSAW_CATALOGUE_RE = re.compile(
    r"^https?://dane\.um\.warszawa\.pl/(?:pl/|en/)?catalogue/([0-9a-f-]{36})"
)
WARSAW_META_URL = "https://dane.um.warszawa.pl/api/datasets/{uuid}"
WARSAW_ACTION_RE = re.compile(r"https://dane\.um\.warszawa\.pl/api/action/[a-z0-9_]+")
WARSAW_AED_ACTION = "https://dane.um.warszawa.pl/api/action/get_scb_lokalizacja_defibrylatorow"

SNAPSHOT_DIR = Path(__file__).resolve().parent / "fixtures" / "snapshot"


@dataclass
class HttpResponse:
    content: bytes
    content_type: str = ""


class HttpClient:
    """Minimal GET/POST client with retries (stdlib only)."""

    def __init__(self, timeout: int = TIMEOUT, retries: int = RETRIES, backoff: float = 1.0):
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff

    def request(
        self, url: str, data: bytes | None = None, headers: dict[str, str] | None = None
    ) -> HttpResponse:
        last_error: Exception | None = None
        for attempt in range(self.retries):
            try:
                req = urllib.request.Request(
                    url,
                    data=data,
                    headers={"User-Agent": USER_AGENT, "Accept": "*/*", **(headers or {})},
                )
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:  # noqa: S310
                    return HttpResponse(resp.read(), resp.headers.get("Content-Type", ""))
            except urllib.error.HTTPError as exc:
                if exc.code in (401, 403):
                    raise PermissionError(f"{url}: HTTP {exc.code}") from exc
                last_error = exc
                logger.warning("GET %s failed (attempt %s): %s", url, attempt + 1, exc)
                if attempt + 1 < self.retries:
                    time.sleep(self.backoff * (attempt + 1))
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                last_error = exc
                logger.warning("GET %s failed (attempt %s): %s", url, attempt + 1, exc)
                if attempt + 1 < self.retries:
                    time.sleep(self.backoff * (attempt + 1))
        raise ConnectionError(f"{url}: {last_error}")

    def get(self, url: str) -> HttpResponse:
        return self.request(url)

    def get_json(self, url: str) -> dict:
        return json.loads(self.get(url).content)


@dataclass
class HarvestReport:
    datasets: list[SourceDataset] = field(default_factory=list)
    resources: list[SourceResource] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


# --- dane.gov.pl ---------------------------------------------------------------------------


def discover_dane_dataset_ids(client: HttpClient) -> list[str]:
    """Find ids of datasets on dane.gov.pl that contain AED data (via the public search API)."""
    found: dict[str, None] = {}
    for query in SEARCH_QUERIES:
        url = f"{DANE_API_URL}/search?" + urllib.parse.urlencode({"q": query, "per_page": 100})
        for _ in range(SEARCH_MAX_PAGES):
            payload = client.get_json(url)
            for item in payload.get("data", []):
                attrs = item.get("attributes", {})
                title = re.sub(r"<[^>]+>", "", attrs.get("title") or "")
                if not AED_TITLE_RE.search(title):
                    continue
                model = attrs.get("model")
                if model == "dataset":
                    found[str(item["id"])] = None
                elif model == "resource":
                    rel = item.get("relationships", {}).get("dataset", {}).get("data") or {}
                    if rel.get("id"):
                        found[str(rel["id"])] = None
            url = payload.get("links", {}).get("next")
            if not url:
                break
    return list(found)


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = parse_datetime(value)
    if parsed and timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed)
    return parsed


def _institution_title(client: HttpClient, dataset_payload: dict, cache: dict[str, str]) -> str:
    rel = dataset_payload.get("relationships", {}).get("institution", {})
    inst_id = (rel.get("data") or {}).get("id")
    if not inst_id:
        return ""
    if inst_id not in cache:
        try:
            inst = client.get_json(f"{DANE_API_URL}/institutions/{inst_id}")
            cache[inst_id] = inst["data"]["attributes"].get("title", "")
        except (ConnectionError, KeyError, ValueError):
            cache[inst_id] = ""
    return cache[inst_id]


def harvest_dane_dataset(
    client: HttpClient, dataset_id: str, institutions: dict[str, str]
) -> tuple[SourceDataset, list[SourceResource]]:
    """Fetch metadata + resources of one dane.gov.pl dataset and store them."""
    payload = client.get_json(f"{DANE_API_URL}/datasets/{dataset_id}")["data"]
    attrs = payload["attributes"]
    dataset, _ = SourceDataset.objects.update_or_create(
        kind=SourceDataset.Kind.DANE_GOV_PL,
        external_id=dataset_id,
        defaults={
            "title": attrs.get("title", "")[:500],
            "publisher": _institution_title(client, payload, institutions)[:500],
            "url": f"{DANE_PORTAL_URL}/{dataset_id}",
            "api_url": f"{DANE_API_URL}/datasets/{dataset_id}",
            "license_name": attrs.get("license_name") or "",
            "source_modified": _parse_dt(attrs.get("modified")),
        },
    )
    dataset_is_aed = bool(AED_TITLE_RE.search(dataset.title))
    res_payload = client.get_json(f"{DANE_API_URL}/datasets/{dataset_id}/resources?per_page=100")
    resources = []
    for item in res_payload.get("data", []):
        r_attrs = item["attributes"]
        title = r_attrs.get("title") or ""
        # Mixed datasets (e.g. "Zdrowie" with pharmacies + AEDs): keep only AED resources.
        if not dataset_is_aed and not AED_TITLE_RE.search(title):
            continue
        url = r_attrs.get("file_url") or r_attrs.get("link") or ""
        if not url:
            continue
        resource, _ = SourceResource.objects.update_or_create(
            dataset=dataset,
            external_id=str(item["id"]),
            defaults={
                "title": title[:500],
                "format": (r_attrs.get("format") or "").lower(),
                "url": url,
            },
        )
        resources.append(resource)
    return dataset, resources


# --- OpenStreetMap -------------------------------------------------------------------------


def harvest_osm(client: HttpClient) -> tuple[SourceDataset, SourceResource]:
    """Store the OSM AED dataset; download from OpenAEDMap, fall back to Overpass."""
    dataset, _ = SourceDataset.objects.update_or_create(
        kind=SourceDataset.Kind.OSM,
        external_id=OSM_DATASET_ID,
        defaults={
            "title": "OpenStreetMap – defibrylatory AED w Polsce",
            "publisher": "Współtwórcy OpenStreetMap (eksport OpenAEDMap)",
            "url": "https://openaedmap.org/",
            "api_url": OSM_PRIMARY_URL,
            "license_name": "ODbL 1.0",
        },
    )
    resource, _ = SourceResource.objects.update_or_create(
        dataset=dataset,
        external_id="pl-geojson",
        defaults={"title": "AED w Polsce (GeoJSON)", "format": "geojson", "url": OSM_PRIMARY_URL},
    )
    try:
        response = client.get(OSM_PRIMARY_URL)
        _store_payload(resource, response)
    except ConnectionError as primary_error:
        body = urllib.parse.urlencode({"data": OVERPASS_QUERY}).encode()
        for overpass_url in OVERPASS_URLS:
            try:
                response = client.request(overpass_url, data=body)
                resource.url = overpass_url
                resource.format = "overpass-json"
                _store_payload(resource, response)
                break
            except ConnectionError:
                continue
        else:
            _store_error(resource, f"OpenAEDMap and Overpass unavailable: {primary_error}")
    resource.selected = resource.fetch_status == SourceResource.FetchStatus.OK
    resource.save()
    return dataset, resource


# --- download + selection ------------------------------------------------------------------


def _store_payload(resource: SourceResource, response: HttpResponse) -> None:
    content_type = response.content_type.lower()
    resource.content_type = response.content_type[:200]
    resource.fetched_at = timezone.now()
    resource.size = len(response.content)
    head = response.content[:512].lstrip().lower()
    if any(t in content_type for t in HTML_TYPES) or head.startswith((b"<!doctype html", b"<html")):
        resource.raw = None
        resource.fetch_status = SourceResource.FetchStatus.NOT_MACHINE_READABLE
        resource.fetch_error = "Link leads to an HTML page, not a machine-readable file"
    else:
        resource.raw = response.content
        resource.fetch_status = SourceResource.FetchStatus.OK
        resource.fetch_error = ""


def _store_error(resource: SourceResource, message: str) -> None:
    resource.raw = None
    resource.size = 0
    resource.fetched_at = timezone.now()
    resource.fetch_status = SourceResource.FetchStatus.ERROR
    resource.fetch_error = message[:2000]


def _warsaw_action_url(client: HttpClient, uuid: str) -> str:
    """Resolve the API action of a Warsaw catalogue entry from its published call examples."""
    try:
        meta = client.get_json(WARSAW_META_URL.format(uuid=uuid))
        examples = client.get(meta["call_examples"]).content.decode("utf-8", "ignore")
        match = WARSAW_ACTION_RE.search(examples)
        if match:
            return match.group(0)
    except (ConnectionError, KeyError, ValueError, TypeError):
        pass
    return WARSAW_AED_ACTION


def fetch_warsaw(client: HttpClient, resource: SourceResource, uuid: str) -> None:
    """Download Warsaw AED data via the token-protected city API (WARSAW_API_TOKEN)."""
    token = getattr(settings, "WARSAW_API_TOKEN", "")
    action_url = _warsaw_action_url(client, uuid)
    if not token:
        resource.raw = None
        resource.size = 0
        resource.fetched_at = timezone.now()
        resource.fetch_status = SourceResource.FetchStatus.REQUIRES_API_KEY
        resource.fetch_error = (
            f"dane.gov.pl links to a catalogue page; data available only via {action_url} "
            "with a free API token (set WARSAW_API_TOKEN, see dane.um.warszawa.pl/key-api)"
        )
        return
    try:
        response = client.request(
            action_url,
            data=b"{}",
            headers={"Authorization": token, "Content-Type": "application/json"},
        )
    except PermissionError as exc:
        resource.raw = None
        resource.fetched_at = timezone.now()
        resource.fetch_status = SourceResource.FetchStatus.REQUIRES_API_KEY
        resource.fetch_error = f"Token rejected by Warsaw API: {exc}"
        return
    except ConnectionError as exc:
        _store_error(resource, str(exc))
        return
    _store_payload(resource, response)
    if resource.fetch_status == SourceResource.FetchStatus.OK:
        resource.format = "json"
        resource.fetch_error = f"Fetched via Warsaw API {action_url}"


def download_resources(client: HttpClient, resources: list[SourceResource]) -> None:
    """Download each resource once; same URL or same content within a dataset = duplicate."""
    seen: dict[tuple[int, str], SourceResource] = {}
    hashes: dict[tuple[int, str], SourceResource] = {}
    for resource in resources:
        key = (resource.dataset_id, resource.url)
        if key in seen:
            resource.raw = None
            resource.fetch_status = SourceResource.FetchStatus.DUPLICATE
            resource.fetch_error = f"Same URL as resource #{seen[key].external_id}"
            resource.save()
            continue
        seen[key] = resource
        warsaw = WARSAW_CATALOGUE_RE.match(resource.url)
        if warsaw:
            fetch_warsaw(client, resource, warsaw.group(1))
        else:
            try:
                _store_payload(resource, client.get(resource.url))
            except (ConnectionError, PermissionError) as exc:
                _store_error(resource, str(exc))
        if resource.raw:
            digest = (resource.dataset_id, hashlib.sha256(bytes(resource.raw)).hexdigest())
            if digest in hashes:
                resource.raw = None
                resource.fetch_status = SourceResource.FetchStatus.DUPLICATE
                resource.fetch_error = f"Same content as resource #{hashes[digest].external_id}"
            else:
                hashes[digest] = resource
        resource.save()


def _format_rank(fmt: str) -> int:
    return FORMAT_PRIORITY.index(fmt) if fmt in FORMAT_PRIORITY else len(FORMAT_PRIORITY)


def select_best_resources(dataset: SourceDataset) -> SourceResource | None:
    """Mark the best successfully fetched resource of a dataset as ``selected``."""
    candidates = [
        r for r in dataset.resources.all() if r.fetch_status == SourceResource.FetchStatus.OK
    ]
    best = min(candidates, key=lambda r: (_format_rank(r.format), r.external_id), default=None)
    dataset.resources.update(selected=False)
    if best:
        SourceResource.objects.filter(pk=best.pk).update(selected=True)
    return best


# --- orchestration -------------------------------------------------------------------------


def harvest_all(client: HttpClient | None = None, include_osm: bool = True) -> HarvestReport:
    """Discover and download every AED source. Idempotent (update_or_create everywhere)."""
    client = client or HttpClient()
    report = HarvestReport()
    institutions: dict[str, str] = {}
    try:
        dataset_ids = discover_dane_dataset_ids(client)
    except (ConnectionError, ValueError) as exc:
        report.errors.append(f"dane.gov.pl search failed: {exc}")
        dataset_ids = []
    for dataset_id in dataset_ids:
        try:
            dataset, resources = harvest_dane_dataset(client, dataset_id, institutions)
        except (ConnectionError, KeyError, ValueError) as exc:
            report.errors.append(f"dataset {dataset_id}: {exc}")
            continue
        download_resources(client, resources)
        select_best_resources(dataset)
        report.datasets.append(dataset)
        report.resources.extend(resources)
    if include_osm:
        dataset, resource = harvest_osm(client)
        report.datasets.append(dataset)
        report.resources.append(resource)
    return report


# --- offline snapshot ----------------------------------------------------------------------


def _snapshot_name(resource: SourceResource) -> str:
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", f"{resource.dataset.kind}_{resource.dataset.external_id}")
    return f"{safe}_{resource.external_id}.{resource.format or 'bin'}"


def save_snapshot(directory: Path = SNAPSHOT_DIR) -> int:
    """Write raw payloads of fetched resources + a manifest (offline demo fallback)."""
    directory.mkdir(parents=True, exist_ok=True)
    manifest = []
    for dataset in SourceDataset.objects.prefetch_related("resources"):
        ds_meta = {
            "kind": dataset.kind, "external_id": dataset.external_id, "title": dataset.title,
            "publisher": dataset.publisher, "url": dataset.url, "api_url": dataset.api_url,
            "license_name": dataset.license_name,
            "source_modified": dataset.source_modified.isoformat()
            if dataset.source_modified else None,
            "resources": [],
        }
        for resource in dataset.resources.all():
            entry = {
                "external_id": resource.external_id, "title": resource.title,
                "format": resource.format, "url": resource.url,
                "content_type": resource.content_type, "fetch_status": resource.fetch_status,
                "fetch_error": resource.fetch_error, "selected": resource.selected, "file": None,
            }
            if resource.raw:
                name = _snapshot_name(resource)
                (directory / name).write_bytes(bytes(resource.raw))
                entry["file"] = name
            ds_meta["resources"].append(entry)
        manifest.append(ds_meta)
    (directory / "manifest.json").write_text(
        json.dumps(
            {"generated_at": timezone.now().isoformat(),
             "note": "Offline snapshot of harvested AED sources (demo fallback).",
             "datasets": manifest},
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )
    return len(manifest)


def load_snapshot(directory: Path = SNAPSHOT_DIR) -> HarvestReport:
    """Recreate SourceDataset/SourceResource rows from a saved snapshot (no network)."""
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    report = HarvestReport()
    for ds_meta in manifest["datasets"]:
        dataset, _ = SourceDataset.objects.update_or_create(
            kind=ds_meta["kind"],
            external_id=ds_meta["external_id"],
            defaults={
                "title": ds_meta["title"], "publisher": ds_meta["publisher"],
                "url": ds_meta["url"], "api_url": ds_meta["api_url"],
                "license_name": ds_meta["license_name"],
                "source_modified": _parse_dt(ds_meta.get("source_modified")),
            },
        )
        for entry in ds_meta["resources"]:
            raw = (directory / entry["file"]).read_bytes() if entry.get("file") else None
            resource, _ = SourceResource.objects.update_or_create(
                dataset=dataset,
                external_id=entry["external_id"],
                defaults={
                    "title": entry["title"], "format": entry["format"], "url": entry["url"],
                    "content_type": entry["content_type"], "raw": raw,
                    "size": len(raw) if raw else 0, "fetch_status": entry["fetch_status"],
                    "fetch_error": entry["fetch_error"], "selected": entry["selected"],
                    "fetched_at": timezone.now(),
                },
            )
            report.resources.append(resource)
        report.datasets.append(dataset)
    return report

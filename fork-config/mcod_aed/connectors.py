"""Load the data behind a portal resource or URL as bytes (T14; T13 adds API-specific connectors)."""
import os

import requests

MAX_BYTES = 30 * 1024 * 1024
TIMEOUT = 60

# Connected APIs (DEC-009 / DEC-014)
WARSAW_ACTION_PREFIX = "https://dane.um.warszawa.pl/api/action/"
WARSAW_AED_ACTION = WARSAW_ACTION_PREFIX + "get_scb_lokalizacja_defibrylatorow"
OSM_AED_URL = "https://openaedmap.org/api/v1/countries/PL.geojson"
# Labelled offline copy of the Warsaw API answer (fetched with a token on 2026-11-21), used only when the
# city API is unreachable (e.g. dane.um.warszawa.pl times out from the Hetzner server).
WARSAW_SNAPSHOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "snapshot",
                               "dane_gov_pl_39512_2512040.json")
WARSAW_SNAPSHOT_NAME = "warszawa-aed-kopia-offline-2026-11-21.json"


class SourceLoadError(Exception):
    pass


def fetch_url(url, max_bytes=MAX_BYTES):
    """GET a URL (self-signed TLS allowed, like the fork's own link validation). -> (bytes, filename)."""
    try:
        with requests.get(url, timeout=TIMEOUT, verify=False, stream=True,
                          headers={"User-Agent": "dane.gov.pl mcod.aed validator"}) as resp:
            if resp.status_code >= 400:
                raise SourceLoadError("HTTP {} dla {}".format(resp.status_code, url))
            chunks, size = [], 0
            for chunk in resp.iter_content(64 * 1024):
                size += len(chunk)
                if size > max_bytes:
                    raise SourceLoadError("Dane pod adresem są większe niż {} MB.".format(max_bytes // 1024 // 1024))
                chunks.append(chunk)
            filename = url.split("?", 1)[0].rstrip("/").rsplit("/", 1)[-1]
            content_type = resp.headers.get("Content-Type", "")
            if "." not in filename:
                if "json" in content_type:
                    filename += ".json"
                elif "csv" in content_type:
                    filename += ".csv"
            return b"".join(chunks), filename
    except requests.RequestException as exc:
        raise SourceLoadError("Nie udało się pobrać {}: {}".format(url, exc))


def fetch_warsaw(url):
    """Warsaw city API: POST with the free token from https://dane.um.warszawa.pl/key-api."""
    token = os.environ.get("WARSAW_API_TOKEN", "").strip()
    if not token:
        raise SourceLoadError(
            "API m.st. Warszawy wymaga tokenu (WARSAW_API_TOKEN, bezpłatny: dane.um.warszawa.pl/key-api)."
        )
    try:
        resp = requests.post(url, data=b"{}", timeout=(10, TIMEOUT),
                             headers={"Authorization": token, "Content-Type": "application/json",
                                      "User-Agent": "dane.gov.pl mcod.aed"})
    except requests.RequestException as exc:
        if os.path.exists(WARSAW_SNAPSHOT):  # unreachable network path -> labelled offline copy
            with open(WARSAW_SNAPSHOT, "rb") as fh:
                return fh.read(), WARSAW_SNAPSHOT_NAME
        raise SourceLoadError("Nie udało się pobrać {}: {}".format(url, exc))
    if resp.status_code in (401, 403):
        raise SourceLoadError("API m.st. Warszawy odrzuciło token (HTTP {}).".format(resp.status_code))
    if resp.status_code >= 400:
        raise SourceLoadError("HTTP {} dla {}".format(resp.status_code, url))
    return resp.content, "warszawa-aed.json"


def fetch_link(url, max_bytes=MAX_BYTES):
    """Connected API / link -> (bytes, filename)."""
    if url.startswith(WARSAW_ACTION_PREFIX):
        return fetch_warsaw(url)
    return fetch_url(url, max_bytes=max_bytes)


def resource_bytes(resource):
    """Data of a portal resource: its uploaded main file, else its link. -> (bytes, filename, format_hint)."""
    if resource.link and getattr(resource, "type", None) == "api" and not resource.is_link_internal:
        data, filename = fetch_link(resource.link)  # connected API: always live data
        return data, filename, None
    main_file = getattr(resource, "main_file", None)
    if main_file:
        try:
            path = main_file.path
            with open(path, "rb") as fh:
                return fh.read(), os.path.basename(path), resource.format
        except (OSError, ValueError, NotImplementedError):
            pass
    if resource.link:
        data, filename = fetch_link(resource.link)
        return data, filename, None
    raise SourceLoadError("Zasób {} nie ma pliku ani linku.".format(resource.pk))

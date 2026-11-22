"""Load the data behind a portal resource or URL as bytes (T14; T13 adds API-specific connectors)."""
import os

import requests

MAX_BYTES = 30 * 1024 * 1024
TIMEOUT = 60


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


def resource_bytes(resource):
    """Data of a portal resource: its uploaded main file, else its link. -> (bytes, filename, format_hint)."""
    main_file = getattr(resource, "main_file", None)
    if main_file:
        try:
            path = main_file.path
            with open(path, "rb") as fh:
                return fh.read(), os.path.basename(path), resource.format
        except (OSError, ValueError, NotImplementedError):
            pass
    if resource.link:
        data, filename = fetch_url(resource.link)
        return data, filename, None
    raise SourceLoadError("Zasób {} nie ma pliku ani linku.".format(resource.pk))

"""Parse raw source payloads into rows: ``(row_id, properties: dict, lon, lat)``.

Coordinates found in a geometry are returned as-is; tabular coordinates stay in the
properties and are picked up by the mapping step (``normalize.py``).
"""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Iterator
from dataclasses import dataclass

from openpyxl import load_workbook


@dataclass
class RawRow:
    row_id: str
    props: dict
    lon: float | None = None
    lat: float | None = None


class ParseError(ValueError):
    """Raised when a payload cannot be parsed in the declared format."""


def decode_text(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1250", "iso-8859-2"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace")


def _unwrap_row_quoting(text: str) -> str:
    """Fix CSVs where every whole line is wrapped in quotes and inner quotes doubled (Marki)."""
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) >= 2 and all(
        line.startswith('"') and line.endswith('"') and line.count(",") >= 1 for line in lines
    ):
        first = next(csv.reader([lines[0]]))
        if len(first) == 1:  # whole header is a single quoted cell
            return "\n".join(line[1:-1].replace('""', '"') for line in lines)
    return text


def parse_csv(raw: bytes) -> list[RawRow]:
    text = _unwrap_row_quoting(decode_text(raw))
    sample = text[:5000]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ";" if sample.count(";") > sample.count(",") else ","
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    rows = list(reader)
    if not rows:
        raise ParseError("empty CSV")
    header = [h.strip() for h in rows[0]]
    result = []
    for i, values in enumerate(rows[1:], start=1):
        if not any(v.strip() for v in values):
            continue
        props = {header[j]: values[j].strip() for j in range(min(len(header), len(values)))}
        result.append(RawRow(row_id=str(i), props=props))
    return result


def parse_xlsx(raw: bytes) -> list[RawRow]:
    wb = load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    ws = wb.worksheets[0]
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise ParseError("empty workbook")
    header = [str(h).strip() if h is not None else "" for h in rows[0]]
    result = []
    for i, values in enumerate(rows[1:], start=1):
        if not any(v not in (None, "") for v in values):
            continue
        props = {
            header[j]: ("" if values[j] is None else str(values[j]).strip())
            for j in range(min(len(header), len(values)))
            if header[j]
        }
        result.append(RawRow(row_id=str(i), props=props))
    return result


def _point(geometry: dict | None) -> tuple[float | None, float | None]:
    """Return (lon, lat) of a Point; tolerates Warsaw's nested ``[[lon, lat]]``."""
    if not geometry:
        return None, None
    coords = geometry.get("coordinates")
    while isinstance(coords, list) and coords and isinstance(coords[0], list):
        coords = coords[0]
    if isinstance(coords, list) and len(coords) >= 2:
        try:
            return float(coords[0]), float(coords[1])
        except (TypeError, ValueError):
            return None, None
    return None, None


def _features(payload) -> Iterator[dict]:
    if isinstance(payload, dict):
        if isinstance(payload.get("features"), list):
            yield from payload["features"]
            return
        for key in ("result", "data", "items"):
            if isinstance(payload.get(key), list):
                yield from payload[key]
                return
        raise ParseError("JSON object without a list of features")
    if isinstance(payload, list):
        yield from payload
        return
    raise ParseError("unsupported JSON structure")


def parse_geojson(raw: bytes) -> list[RawRow]:
    """GeoJSON FeatureCollection or a plain list of feature-like objects (Warsaw API)."""
    try:
        payload = json.loads(decode_text(raw))
    except json.JSONDecodeError as exc:
        raise ParseError(f"invalid JSON: {exc}") from exc
    result = []
    for i, feature in enumerate(_features(payload), start=1):
        if not isinstance(feature, dict):
            continue
        props = feature.get("properties")
        if props is None:  # flat objects
            props = {k: v for k, v in feature.items() if k != "geometry"}
        lon, lat = _point(feature.get("geometry"))
        row_id = str(
            props.get("@osm_type", "") + "/" + str(props["@osm_id"])
            if "@osm_id" in props
            else props.get("defibrillator_id") or props.get("id") or feature.get("id") or i
        )
        result.append(RawRow(row_id=row_id, props=props, lon=lon, lat=lat))
    return result


def parse_overpass(raw: bytes) -> list[RawRow]:
    payload = json.loads(decode_text(raw))
    result = []
    for element in payload.get("elements", []):
        lat = element.get("lat", (element.get("center") or {}).get("lat"))
        lon = element.get("lon", (element.get("center") or {}).get("lon"))
        props = dict(element.get("tags", {}))
        props["@osm_type"] = element.get("type")
        props["@osm_id"] = element.get("id")
        result.append(
            RawRow(
                row_id=f"{element.get('type')}/{element.get('id')}", props=props, lon=lon, lat=lat
            )
        )
    return result


PARSERS = {
    "csv": parse_csv,
    "xlsx": parse_xlsx,
    "geojson": parse_geojson,
    "json": parse_geojson,
    "overpass-json": parse_overpass,
}


def parse(fmt: str, raw: bytes) -> list[RawRow]:
    parser = PARSERS.get(fmt)
    if parser is None:
        raise ParseError(f"no parser for format '{fmt}'")
    return parser(raw)

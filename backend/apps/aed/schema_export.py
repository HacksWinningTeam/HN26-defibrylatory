"""Render the standard AED schema (``apps.aed.schema``) into downloadable artefacts."""

from __future__ import annotations

import csv
import io
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from apps.aed.schema import (
    BOOLEAN,
    DATE,
    FIELDS,
    GROUPS,
    INTEGER,
    NUMBER,
    OBLIGATIONS,
    REQUIRED_FIELDS,
    SCHEMA_DESCRIPTION,
    SCHEMA_NAME,
    SCHEMA_TITLE,
    SCHEMA_TITLE_EN,
    SCHEMA_VERSION,
    FieldSpec,
    example_rows,
)

LICENSE_NAME = "CC BY 4.0"
LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/deed.pl"

XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

TYPE_LABELS_PL = {
    "string": "tekst",
    NUMBER: "liczba dziesiętna",
    INTEGER: "liczba całkowita",
    BOOLEAN: "logiczna (true/false)",
    DATE: "data (YYYY-MM-DD)",
}


def format_value(value: Any) -> str:
    """Format a Python value as a CSV/xlsx cell following the schema conventions."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def field_to_dict(spec: FieldSpec) -> dict[str, Any]:
    """Serialize a field spec to a JSON-friendly dict (used by the API)."""
    return {
        "name": spec.name,
        "group": spec.group,
        "group_label": GROUPS[spec.group],
        "type": spec.type,
        "obligation": spec.obligation,
        "required": spec.required,
        "label": spec.label,
        "description": spec.description,
        "description_en": spec.description_en,
        "example": format_value(spec.example),
        "allowed_values": [{"value": v, "label": label} for v, label in spec.allowed_values],
        "pattern": spec.pattern,
        "minimum": spec.minimum,
        "maximum": spec.maximum,
        "max_length": spec.max_length,
        "osm_tag": spec.osm_tag,
    }


def schema_document() -> dict[str, Any]:
    """Full schema description returned by ``GET /api/schema-standard/``."""
    return {
        "name": SCHEMA_NAME,
        "version": SCHEMA_VERSION,
        "title": SCHEMA_TITLE,
        "title_en": SCHEMA_TITLE_EN,
        "description": SCHEMA_DESCRIPTION,
        "license": LICENSE_NAME,
        "obligations": list(OBLIGATIONS),
        "groups": [{"code": code, "label": label} for code, label in GROUPS.items()],
        "fields": [field_to_dict(f) for f in FIELDS],
    }


# --- JSON Schema ---------------------------------------------------------------------------


def _json_schema_property(spec: FieldSpec) -> dict[str, Any]:
    prop: dict[str, Any] = {"title": spec.label, "description": spec.description}
    if spec.type == DATE:
        prop.update({"type": "string", "format": "date"})
    elif spec.type in (NUMBER, INTEGER, BOOLEAN):
        prop["type"] = spec.type
    else:
        prop["type"] = "string"
    if spec.allowed_values:
        prop["enum"] = spec.allowed_codes
    if spec.pattern:
        prop["pattern"] = spec.pattern
    if spec.minimum is not None:
        prop["minimum"] = spec.minimum
    if spec.maximum is not None:
        prop["maximum"] = spec.maximum
    if spec.max_length is not None:
        prop["maxLength"] = spec.max_length
    if spec.example not in (None, ""):
        prop["examples"] = [spec.example]
    if not spec.required:
        # Optional fields may be published empty (null or empty string in CSV-derived JSON).
        prop = {"anyOf": [prop, {"type": "null"}, {"const": ""}]}
    return prop


def json_schema() -> dict[str, Any]:
    """JSON Schema (draft 2020-12) of a single AED record."""
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"https://dane.gov.pl/schemas/{SCHEMA_NAME}/{SCHEMA_VERSION}/aed.schema.json",
        "title": SCHEMA_TITLE,
        "description": SCHEMA_DESCRIPTION,
        "type": "object",
        "required": list(REQUIRED_FIELDS),
        "properties": {f.name: _json_schema_property(f) for f in FIELDS},
        "additionalProperties": False,
    }


# --- Frictionless Table Schema -------------------------------------------------------------


def table_schema() -> dict[str, Any]:
    """Frictionless Table Schema for the CSV form of the dataset."""
    fields = []
    for spec in FIELDS:
        item: dict[str, Any] = {
            "name": spec.name,
            "title": spec.label,
            "description": spec.description,
            "type": spec.type,
        }
        if spec.type == DATE:
            item["format"] = "%Y-%m-%d"
        if spec.type == BOOLEAN:
            item["trueValues"] = ["true"]
            item["falseValues"] = ["false"]
        constraints: dict[str, Any] = {"required": spec.required}
        if spec.allowed_values:
            constraints["enum"] = spec.allowed_codes
        if spec.pattern:
            constraints["pattern"] = spec.pattern
        if spec.minimum is not None:
            constraints["minimum"] = spec.minimum
        if spec.maximum is not None:
            constraints["maximum"] = spec.maximum
        if spec.max_length is not None:
            constraints["maxLength"] = spec.max_length
        item["constraints"] = constraints
        fields.append(item)
    return {
        "fields": fields,
        "primaryKey": ["id_aed"],
        "missingValues": [""],
    }


# --- CSV template --------------------------------------------------------------------------


def csv_template() -> str:
    """CSV template: header row + illustrative example rows (UTF-8, comma separated)."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\r\n")
    writer.writerow([f.name for f in FIELDS])
    for row in example_rows():
        writer.writerow([format_value(row.get(f.name)) for f in FIELDS])
    return buffer.getvalue()


# --- XLSX ----------------------------------------------------------------------------------

_HEADER_FONT = Font(bold=True, color="FFFFFF")
_HEADER_FILL = PatternFill("solid", fgColor="B91C1C")  # dark red, white text >= 4.5:1
_WRAP = Alignment(wrap_text=True, vertical="top")


def _style_header(ws, widths: list[int]) -> None:
    for idx, width in enumerate(widths, start=1):
        cell = ws.cell(row=1, column=idx)
        cell.font = _HEADER_FONT
        cell.fill = _HEADER_FILL
        cell.alignment = _WRAP
        ws.column_dimensions[get_column_letter(idx)].width = width
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions


def xlsx_bytes() -> bytes:
    """Excel workbook with the schema, examples, code lists and general rules."""
    wb = Workbook()

    ws = wb.active
    ws.title = "Schemat"
    headers = [
        "Lp.", "Nazwa pola (kolumna)", "Grupa", "Etykieta", "Opis", "Typ", "Wymagalność",
        "Format / wzorzec / zakres", "Dozwolone wartości", "Przykład", "Tag OpenStreetMap",
        "Description (EN)",
    ]
    ws.append(headers)
    for i, spec in enumerate(FIELDS, start=1):
        constraints = []
        if spec.pattern:
            constraints.append(f"wzorzec: {spec.pattern}")
        if spec.minimum is not None or spec.maximum is not None:
            constraints.append(f"zakres: {spec.minimum} – {spec.maximum}")
        if spec.max_length is not None:
            constraints.append(f"maks. długość: {spec.max_length}")
        ws.append(
            [
                i, spec.name, GROUPS[spec.group], spec.label, spec.description,
                TYPE_LABELS_PL[spec.type], spec.obligation, "; ".join(constraints),
                ", ".join(spec.allowed_codes) if spec.allowed_values else "",
                format_value(spec.example), spec.osm_tag or "", spec.description_en,
            ]
        )
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = _WRAP
    _style_header(ws, [5, 28, 18, 26, 60, 18, 13, 30, 30, 26, 22, 50])

    ws_ex = wb.create_sheet("Przykład")
    ws_ex.append([f.name for f in FIELDS])
    for row in example_rows():
        ws_ex.append([format_value(row.get(f.name)) for f in FIELDS])
    _style_header(ws_ex, [max(14, len(f.name) + 2) for f in FIELDS])

    ws_dict = wb.create_sheet("Słowniki")
    ws_dict.append(["Pole", "Wartość", "Znaczenie"])
    for spec in FIELDS:
        if spec.allowed_values and spec.name != "wojewodztwo":
            for code, label in spec.allowed_values:
                ws_dict.append([spec.name, code, label])
    _style_header(ws_dict, [22, 22, 70])

    ws_info = wb.create_sheet("Informacje")
    ws_info.append(["Element", "Wartość"])
    for key, value in (
        ("Nazwa", SCHEMA_TITLE),
        ("Wersja", SCHEMA_VERSION),
        ("Opis", SCHEMA_DESCRIPTION),
        ("Format pliku", "CSV (UTF-8, separator przecinek, pierwszy wiersz = nazwy pól) "
                         "lub XLSX / JSON / GeoJSON z tymi samymi nazwami pól"),
        ("Współrzędne", "WGS84 (EPSG:4326), stopnie dziesiętne, kropka jako separator"),
        ("Daty", "ISO 8601: YYYY-MM-DD"),
        ("Wartości logiczne", "true / false"),
        ("Godziny dostępności", "Składnia opening_hours (OpenStreetMap), np. 24/7"),
        ("Pola wymagane", ", ".join(REQUIRED_FIELDS)),
        ("Licencja zalecana", f"{LICENSE_NAME} ({LICENSE_URL})"),
        ("Częstotliwość aktualizacji", "co najmniej raz w miesiącu oraz po każdej zmianie"),
        ("Uwaga", "Wiersze w arkuszu 'Przykład' są przykładowe (ilustracyjne)."),
    ):
        ws_info.append([key, value])
    for row in ws_info.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = _WRAP
    _style_header(ws_info, [28, 100])

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()

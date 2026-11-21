"""Tests for the standard AED schema and its downloadable artefacts (T01)."""

import csv
import io
import json
import re

import jsonschema
import pytest
from openpyxl import load_workbook
from rest_framework.test import APIClient

from apps.aed import schema_export
from apps.aed.schema import (
    FIELD_NAMES,
    FIELDS,
    GROUPS,
    OBLIGATIONS,
    REQUIRED_FIELDS,
    TYPES,
    example_rows,
)


def test_field_names_are_unique_ascii_snake_case() -> None:
    assert len(FIELD_NAMES) == len(set(FIELD_NAMES))
    for name in FIELD_NAMES:
        assert re.fullmatch(r"[a-z][a-z0-9_]*", name), name


def test_field_specs_are_consistent() -> None:
    for spec in FIELDS:
        assert spec.group in GROUPS
        assert spec.type in TYPES
        assert spec.obligation in OBLIGATIONS
        assert spec.label and spec.description and spec.description_en


def test_required_core_fields() -> None:
    for name in (
        "id_aed", "nazwa", "szerokosc_geograficzna", "dlugosc_geograficzna",
        "miejscowosc", "dostep", "zrodlo", "data_aktualizacji",
    ):
        assert name in REQUIRED_FIELDS
    # Keep the entry barrier low for data owners.
    assert len(REQUIRED_FIELDS) <= 10


def _validator() -> jsonschema.Draft202012Validator:
    schema = schema_export.json_schema()
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER
    )


def test_json_schema_accepts_example_rows() -> None:
    validator = _validator()
    for row in example_rows():
        assert list(validator.iter_errors(row)) == []


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("szerokosc_geograficzna", 200),
        ("dlugosc_geograficzna", 5.0),
        ("kod_pocztowy", "05120"),
        ("dostep", "dla_wszystkich"),
        ("zabezpieczenie", "sejf"),
        ("data_aktualizacji", "21.11.2026"),
        ("kod_terc", "140801"),
    ],
)
def test_json_schema_rejects_invalid_values(field: str, value: object) -> None:
    row = example_rows()[0] | {field: value}
    assert list(_validator().iter_errors(row)) != []


def test_json_schema_rejects_missing_required_field() -> None:
    row = dict(example_rows()[0])
    del row["nazwa"]
    assert list(_validator().iter_errors(row)) != []


def test_json_schema_allows_empty_optional_field() -> None:
    row = example_rows()[0] | {"pietro": None, "producent": ""}
    assert list(_validator().iter_errors(row)) == []


def test_table_schema_matches_fields() -> None:
    ts = schema_export.table_schema()
    assert [f["name"] for f in ts["fields"]] == list(FIELD_NAMES)
    required = [f["name"] for f in ts["fields"] if f["constraints"]["required"]]
    assert required == list(REQUIRED_FIELDS)


def test_csv_template_header_and_examples() -> None:
    rows = list(csv.reader(io.StringIO(schema_export.csv_template())))
    assert rows[0] == list(FIELD_NAMES)
    assert len(rows) == 1 + len(example_rows())
    lat_idx = rows[0].index("szerokosc_geograficzna")
    assert float(rows[1][lat_idx]) == pytest.approx(52.395198)


def test_xlsx_workbook_structure() -> None:
    wb = load_workbook(io.BytesIO(schema_export.xlsx_bytes()))
    assert wb.sheetnames == ["Schemat", "Przykład", "Słowniki", "Informacje"]
    schema_ws = wb["Schemat"]
    names = [row[1] for row in schema_ws.iter_rows(min_row=2, values_only=True)]
    assert names == list(FIELD_NAMES)
    example_header = [c.value for c in wb["Przykład"][1]]
    assert example_header == list(FIELD_NAMES)


@pytest.mark.django_db
def test_schema_document_endpoint() -> None:
    response = APIClient().get("/api/schema-standard/")
    assert response.status_code == 200
    body = response.json()
    assert body["version"] == "1.0.0"
    assert [f["name"] for f in body["fields"]] == list(FIELD_NAMES)
    dostep = next(f for f in body["fields"] if f["name"] == "dostep")
    assert dostep["required"] is True
    assert {v["value"] for v in dostep["allowed_values"]} >= {"publiczny", "nieznany"}


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("path", "content_type", "filename"),
    [
        ("aed-schema.xlsx", schema_export.XLSX_CONTENT_TYPE, "aed-schema.xlsx"),
        ("aed-template.csv", "text/csv", "aed-template.csv"),
        ("aed-schema.json", "application/schema+json", "aed-schema.json"),
        ("table-schema.json", "application/schema+json", "table-schema.json"),
    ],
)
def test_schema_downloads(path: str, content_type: str, filename: str) -> None:
    response = APIClient().get(f"/api/schema-standard/{path}")
    assert response.status_code == 200
    assert response["Content-Type"].startswith(content_type)
    assert f'filename="{filename}"' in response["Content-Disposition"]
    if path.endswith(".json"):
        assert json.loads(response.content)


def test_export_schema_command(tmp_path) -> None:
    from django.core.management import call_command

    call_command("export_schema", out=str(tmp_path))
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "aed-schema.json", "aed-schema.xlsx", "aed-template.csv", "table-schema.json",
    ]


def test_london_compatible_fields_present() -> None:
    """Fields added for compatibility with the London-based AED schema (DEC-007)."""
    from apps.aed.schema import FIELDS_BY_NAME

    for name in (
        "numer_seryjny", "data_instalacji", "data_ostatniego_uzycia",
        "data_nastepnego_przegladu", "data_waznosci_elektrod_pediatrycznych",
    ):
        assert name in FIELDS_BY_NAME
        assert not FIELDS_BY_NAME[name].required
    statuses = FIELDS_BY_NAME["status"].allowed_codes
    assert {"do_weryfikacji", "skradziony", "wycofany"} <= set(statuses)
    # Sensitive data must never be part of the open schema.
    assert not {"kod_dostepu", "osoba_kontaktowa"} & set(FIELD_NAMES)

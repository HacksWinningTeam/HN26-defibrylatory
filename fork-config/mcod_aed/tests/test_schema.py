"""Standard AED schema + downloadable artefacts (ported from backend/apps/aed/tests/test_schema.py)."""
import csv
import io
import re
import unittest

import jsonschema
from openpyxl import load_workbook

from mcod.aed import schema_export
from mcod.aed.schema import FIELD_NAMES, FIELDS, GROUPS, OBLIGATIONS, REQUIRED_FIELDS, TYPES, example_rows


def _validator():
    js = schema_export.json_schema()
    jsonschema.Draft202012Validator.check_schema(js)
    return jsonschema.Draft202012Validator(js, format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER)


def _row(**overrides):
    row = dict(example_rows()[0])
    row.update(overrides)
    return row


class SchemaTests(unittest.TestCase):
    def test_field_names_unique_ascii_snake_case(self):
        self.assertEqual(len(FIELD_NAMES), len(set(FIELD_NAMES)))
        for name in FIELD_NAMES:
            self.assertRegex(name, r"^[a-z][a-z0-9_]*$")

    def test_field_specs_consistent(self):
        self.assertEqual(len(FIELDS), 42)
        for spec in FIELDS:
            self.assertIn(spec.group, GROUPS)
            self.assertIn(spec.type, TYPES)
            self.assertIn(spec.obligation, OBLIGATIONS)
            self.assertTrue(spec.label and spec.description and spec.description_en)

    def test_required_core_fields(self):
        for name in ("id_aed", "nazwa", "szerokosc_geograficzna", "dlugosc_geograficzna",
                     "miejscowosc", "dostep", "zrodlo", "data_aktualizacji"):
            self.assertIn(name, REQUIRED_FIELDS)
        self.assertLessEqual(len(REQUIRED_FIELDS), 10)

    def test_json_schema_accepts_examples(self):
        validator = _validator()
        for row in example_rows():
            self.assertEqual(list(validator.iter_errors(row)), [])

    def test_json_schema_rejects_invalid_values(self):
        cases = [("szerokosc_geograficzna", 200), ("dlugosc_geograficzna", 5.0), ("kod_pocztowy", "05120"),
                 ("dostep", "dla_wszystkich"), ("zabezpieczenie", "sejf"),
                 ("data_aktualizacji", "21.11.2026"), ("kod_terc", "140801")]
        validator = _validator()
        for field, value in cases:
            with self.subTest(field=field):
                self.assertNotEqual(list(validator.iter_errors(_row(**{field: value}))), [])

    def test_json_schema_missing_required_and_empty_optional(self):
        row = _row()
        del row["nazwa"]
        self.assertNotEqual(list(_validator().iter_errors(row)), [])
        self.assertEqual(list(_validator().iter_errors(_row(pietro=None, producent=""))), [])

    def test_table_schema_and_csv_template(self):
        ts = schema_export.table_schema()
        self.assertEqual([f["name"] for f in ts["fields"]], list(FIELD_NAMES))
        rows = list(csv.reader(io.StringIO(schema_export.csv_template())))
        self.assertEqual(rows[0], list(FIELD_NAMES))
        self.assertEqual(len(rows), 1 + len(example_rows()))

    def test_xlsx_workbook_structure(self):
        wb = load_workbook(io.BytesIO(schema_export.xlsx_bytes()))
        self.assertEqual(wb.sheetnames, ["Schemat", "Przykład", "Słowniki", "Informacje"])
        names = [row[1] for row in wb["Schemat"].iter_rows(min_row=2, values_only=True)]
        self.assertEqual(names, list(FIELD_NAMES))


if __name__ == "__main__":
    unittest.main()

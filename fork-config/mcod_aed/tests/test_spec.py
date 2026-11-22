"""Data-defined standards (T16, DEC-019). DB writes are rolled back."""
import csv
import io
import json
import os
import unittest

import jsonschema
from django.db import transaction
from openpyxl import load_workbook

from mcod.aed import schema
from mcod.aed.spec import StandardDefinitionError, StandardSpec, aed_definition
from mcod.aed.standards import STANDARDS_DIR

ZLOBKI = os.path.join(STANDARDS_DIR, "zlobki-pl.json")


class _Rollback(Exception):
    pass


def zlobki():
    with open(ZLOBKI, encoding="utf-8") as fh:
        return StandardSpec.from_dict(json.load(fh))


def example_row(spec):
    return {f["name"]: f["example"] for f in spec.fields if f.get("example") is not None}


class SpecTests(unittest.TestCase):
    def test_zlobki_definition(self):
        spec = zlobki()
        self.assertEqual(spec.code, "zlobki-pl")
        self.assertEqual(len(spec.fields), 22)
        self.assertEqual(spec.required, ["id_placowki", "nazwa", "podmiot_prowadzacy", "miejscowosc",
                                         "liczba_miejsc", "data_aktualizacji", "zrodlo"])
        self.assertEqual(set(spec.derivable), {"id_placowki", "data_aktualizacji", "zrodlo"})
        self.assertEqual(spec.merge["strategy"], "key")
        self.assertEqual(spec.geo_fields, ("szerokosc_geograficzna", "dlugosc_geograficzna"))

    def test_synonyms_cover_real_headers(self):
        mapping = zlobki().synonym_map()
        from mcod.aed.normalize import norm_key

        real = {  # headers seen in nursery files on dane.gov.pl
            "nazwa_zlobka": "nazwa", "Nazwa podmiotu": "nazwa", "nazwa_podmiotu_prowadzacego": "podmiot_prowadzacy",
            "address": "adres", "adres_ulica": "ulica", "adres_nr": "nr_budynku", "miejscowo": "miejscowosc",
            "numer budynku": "nr_budynku", "nr telefonu": "telefon", "adres e-mail": "email",
            "max. liczba miejsc w obku": "liczba_miejsc", "lat": "szerokosc_geograficzna",
            "dugo geograficzna podmiotu": "dlugosc_geograficzna", "data_wprowadzonych_zmian": "data_aktualizacji",
            "regon": "regon", "liczba_miejsc": "liczba_miejsc",
        }
        for header, field in real.items():
            with self.subTest(header=header):
                self.assertEqual(mapping.get(norm_key(header)), field)

    def test_json_schema_accepts_example_and_rejects_invalid(self):
        spec = zlobki()
        js = spec.json_schema()
        jsonschema.Draft202012Validator.check_schema(js)
        validator = jsonschema.Draft202012Validator(js, format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER)
        row = example_row(spec)
        self.assertEqual(list(validator.iter_errors(row)), [])
        for field, value in (("liczba_miejsc", "dużo"), ("kod_pocztowy", "43100"), ("typ", "przedszkole"),
                             ("regon", "12"), ("data_wpisu", "01.03.2024")):
            with self.subTest(field=field):
                bad = dict(row)
                bad[field] = value
                self.assertNotEqual(list(validator.iter_errors(bad)), [])
        missing = dict(row)
        del missing["nazwa"]
        self.assertNotEqual(list(validator.iter_errors(missing)), [])

    def test_table_schema_csv_template_xlsx(self):
        spec = zlobki()
        self.assertEqual([f["name"] for f in spec.table_schema()["fields"]], spec.names)
        rows = list(csv.reader(io.StringIO(spec.csv_template())))
        self.assertEqual(rows[0], spec.names)
        wb = load_workbook(io.BytesIO(spec.xlsx_bytes()))
        self.assertEqual(wb.sheetnames, ["Schemat", "Szablon", "Informacje"])
        self.assertEqual([r[1] for r in wb["Schemat"].iter_rows(min_row=2, values_only=True)], spec.names)

    def test_invalid_definitions_rejected(self):
        base = {"code": "x", "name": "X", "fields": [{"name": "a"}]}
        StandardSpec.from_dict(base)  # minimal valid
        for broken in (
            {"fields": []},
            {"fields": [{"name": "Zła Nazwa"}]},
            {"fields": [{"name": "a"}, {"name": "a"}]},
            {"fields": [{"name": "a", "type": "money"}]},
            {"fields": [{"name": "a", "obligation": "czasem"}]},
            {"merge": {"strategy": "magic"}},
        ):
            with self.subTest(broken=broken):
                data = dict(base)
                data.update(broken)
                with self.assertRaises(StandardDefinitionError):
                    StandardSpec.from_dict(data)
        with self.assertRaises(StandardDefinitionError):
            StandardSpec.from_dict({"name": "no code", "fields": [{"name": "a"}]})

    def test_aed_mirror_matches_code_schema(self):
        definition = aed_definition()
        spec = StandardSpec.from_dict(definition)
        self.assertEqual(spec.names, list(schema.FIELD_NAMES))
        self.assertEqual(spec.required, list(schema.REQUIRED_FIELDS))
        self.assertIn("numer_id", spec.by_name["id_aed"]["synonyms"])
        self.assertEqual(spec.merge["strategy"], "geo")


class StandardModelTests(unittest.TestCase):
    def test_load_standard_and_spec_from_model(self):
        from mcod.aed.models import DataStandard
        from mcod.aed.standards import load_standard

        with open(ZLOBKI, encoding="utf-8") as fh:
            data = json.load(fh)
        try:
            with transaction.atomic():
                data["code"] = "zlobki-test"
                standard, created = load_standard(data)
                self.assertTrue(created)
                self.assertEqual(standard.spec().required[1], "nazwa")
                self.assertIn("properties", standard.json_schema)
                data["version"] = "1.0.1"
                standard, created = load_standard(data)
                self.assertFalse(created)
                self.assertEqual(DataStandard.objects.get(code="zlobki-test").version, "1.0.1")
                with self.assertRaises(ValueError):
                    load_standard(dict(data, code="aed-pl"))
                raise _Rollback
        except _Rollback:
            pass

    def test_aed_standard_has_mirrored_fields(self):
        from mcod.aed.models import DataStandard

        aed = DataStandard.objects.get(code="aed-pl")
        self.assertEqual(len(aed.fields), 42)
        self.assertEqual(aed.spec().names, list(schema.FIELD_NAMES))

    def test_seed_migration_works_with_historical_model(self):
        """Migration 0002 runs ensure_aed_standard with the model as it was before 0006 (fresh installs)."""
        from django.db import connection
        from django.db.migrations.executor import MigrationExecutor

        from mcod.aed.standards import ensure_aed_standard

        state = MigrationExecutor(connection).loader.project_state(("aed", "0002_seed_aed_standard"))
        Historical = state.apps.get_model("aed", "DataStandard")
        self.assertNotIn("fields", {f.name for f in Historical._meta.get_fields()})
        try:
            with transaction.atomic():
                standard = ensure_aed_standard(Historical)
                self.assertEqual(standard.code, "aed-pl")
                raise _Rollback
        except _Rollback:
            pass


if __name__ == "__main__":
    unittest.main()


class AggregationDispatchTests(unittest.TestCase):
    """Regression: the admin button of one standard must never run another standard's aggregation."""

    def test_only_supported_standards_are_aggregated(self):
        from unittest import mock

        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.test import RequestFactory

        from mcod.aed import admin as aed_admin
        from mcod.aed.aggregate import run_aggregation, supports_aggregation
        from mcod.aed.models import DataStandard

        aed = DataStandard.objects.get(code="aed-pl")
        zlobki_model = DataStandard(code="zlobki-x", name="Żłobki", version="1", fields=[{"name": "nazwa"}])
        self.assertTrue(supports_aggregation(aed))
        self.assertFalse(supports_aggregation(zlobki_model))
        with self.assertRaises(ValueError):
            run_aggregation(triggered_by="test", standard=zlobki_model)

        request = RequestFactory().get("/")
        request.user = mock.Mock(email="t@example.org")
        request.session = {}
        request._messages = FallbackStorage(request)
        with mock.patch("mcod.aed.tasks.aggregate_task.apply_async") as queued:
            self.assertFalse(aed_admin.queue_aggregation(request, zlobki_model))
            queued.assert_not_called()
            self.assertTrue(aed_admin.queue_aggregation(request, aed))
            self.assertEqual(queued.call_args[1]["kwargs"]["standard_code"], "aed-pl")

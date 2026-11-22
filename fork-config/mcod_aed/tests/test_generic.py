"""Generic validation for data-defined standards (T17, DEC-019). DB writes are rolled back."""
import json
import os
import unittest

from django.db import transaction

from mcod.aed import generic, validation
from mcod.aed.spec import StandardSpec
from mcod.aed.standards import STANDARDS_DIR

SAMPLES = os.path.join(os.path.dirname(__file__), "samples")


class _Rollback(Exception):
    pass


def spec():
    with open(os.path.join(STANDARDS_DIR, "zlobki-pl.json"), encoding="utf-8") as fh:
        return StandardSpec.from_dict(json.load(fh))


def sample(name):
    with open(os.path.join(SAMPLES, name), "rb") as fh:
        return fh.read()


def validate(name, **kwargs):
    rows, fmt = validation.parse_bytes(sample(name), filename=name)
    return generic.validate_rows(rows, spec(), fmt=fmt, **kwargs)


class CoerceTests(unittest.TestCase):
    def test_types(self):
        s = spec()
        places, regon, typ, date_f = (s.by_name[n] for n in ("liczba_miejsc", "regon", "typ", "data_wpisu"))
        self.assertEqual(generic.coerce(places, " 60 "), (60, None, False))
        self.assertEqual(generic.coerce(places, "60,0")[:2], (60, None))
        self.assertEqual(generic.coerce(places, "dużo")[1], "type_integer")
        self.assertEqual(generic.coerce(places, "-1")[1], "minimum")
        self.assertEqual(generic.coerce(places, ""), (None, None, False))
        self.assertEqual(generic.coerce(regon, "276-115-858"), ("276115858", None, True))
        self.assertEqual(generic.coerce(regon, "12")[1], "pattern")
        self.assertEqual(generic.coerce(typ, "Klub dziecięcy"), ("klub_dzieciecy", None, True))
        self.assertEqual(generic.coerce(typ, "przedszkole")[1], "allowed_values")
        self.assertEqual(generic.coerce(date_f, "2024-03-01"), ("2024-03-01", None, False))
        self.assertEqual(generic.coerce(date_f, "2024-03-01 00:00:00"), ("2024-03-01", None, True))
        self.assertEqual(generic.coerce(date_f, "1.3.2024"), ("2024-03-01", None, True))
        self.assertEqual(generic.coerce(date_f, "marzec")[1], "type_date")
        self.assertEqual(generic.coerce(s.by_name["dostosowany_dla_niepelnosprawnych"], "TAK"), (True, None, True))


class GenericValidationTests(unittest.TestCase):
    def test_valid_file(self):
        report = validate("zlobki-valid-demo.csv")
        self.assertEqual((report["standard"], report["status"], report["valid"], report["blocking"]),
                         ("zlobki-pl", "valid", True, False))
        self.assertEqual((report["rows_total"], report["rows_invalid"], report["errors"]), (2, 0, []))
        self.assertEqual(report["coverage"]["required"], 1.0)

    def test_invalid_file(self):
        report = validate("zlobki-invalid-demo.csv")
        self.assertTrue(report["blocking"])
        self.assertEqual(report["rows_invalid"], 3)
        codes = {(e["field"], e["code"]) for e in report["errors"]}
        self.assertEqual(codes, {
            ("liczba_miejsc", "type_integer"), ("regon", "pattern"), ("nazwa", "required"),
            ("typ", "allowed_values"), ("kod_pocztowy", "pattern"), ("liczba_miejsc", "minimum"),
            ("miejscowosc", "required"), ("podmiot_prowadzacy", "required"), ("id_placowki", "duplicate_id"),
        })
        self.assertIn("value_converted", {w["code"] for w in report["warnings"]})  # 22/11/2026

    def test_legacy_headers_mapped_with_warnings(self):
        report = validate("zlobki-legacy-demo.csv")
        self.assertEqual((report["status"], report["blocking"], report["rows_invalid"]), ("warnings", False, 0))
        mapping = report["column_mapping"]
        self.assertEqual(mapping["miejscowo"], {"field": "miejscowosc", "match": "synonym"})
        self.assertEqual(mapping["max. liczba miejsc w obku"]["field"], "liczba_miejsc")
        self.assertEqual(mapping["Nazwa podmiotu"]["field"], "nazwa")
        self.assertEqual(report["missing_required_fields"], ["podmiot_prowadzacy"])
        warnings = {w["code"] for w in report["warnings"]}
        self.assertTrue({"required_derived", "column_synonym", "value_converted"} <= warnings)
        strict = validate("zlobki-legacy-demo.csv", strict=True)
        self.assertTrue(strict["blocking"])

    def test_unmappable_file_blocks(self):
        rows, fmt = validation.parse_bytes(b"a,b\n1,2\n", filename="x.csv")
        report = generic.validate_rows(rows, spec(), fmt=fmt)
        self.assertTrue(report["blocking"])
        self.assertIn("Żadna kolumna", report["blocking_reasons"][0])

    def test_dispatch_aed_vs_generic(self):
        from mcod.aed.models import DataStandard

        aed = DataStandard.objects.get(code="aed-pl")
        zlobki = DataStandard.objects.get(code="zlobki-pl")
        aed_report = validation.validate_for_standard(sample("aed-invalid-demo.csv"), standard=aed, filename="a.csv")
        self.assertEqual((aed_report["standard"], aed_report["rows_invalid"]), ("aed-pl", 3))
        self.assertIn("coordinates_missing", {e["code"] for e in aed_report["errors"]})  # AED-only rule
        z_report = validation.validate_for_standard(sample("zlobki-invalid-demo.csv"), standard=zlobki, filename="z.csv")
        self.assertEqual(z_report["standard"], "zlobki-pl")
        self.assertTrue(z_report["blocking"])


class GenericAutomaticValidationTests(unittest.TestCase):
    def test_nursery_resource_blocked_and_form_refuses(self):
        from django.contrib.auth import get_user_model
        from django.core.files.uploadedfile import SimpleUploadedFile

        from mcod.aed import integration
        from mcod.aed.models import DataStandard, ResourceStandardValidation
        from mcod.aed.resource_validation import validate_resource
        from mcod.datasets.models import Dataset
        from mcod.organizations.models import Organization
        from mcod.resources.models import Resource, ResourceFile

        user = get_user_model().objects.filter(is_superuser=True).first()
        try:
            with transaction.atomic():
                ds = Dataset.objects.create(title="T17 żłobki", organization=Organization.objects.first(),
                                            created_by=user, notes="t", status="published")
                integration.save_dataset_standard(ds, DataStandard.objects.get(code="zlobki-pl"), revalidate=False)
                res = Resource.objects.create(title="T17", dataset=ds, created_by=user, status="published", description="t")
                ResourceFile.objects.create(resource=res, is_main=True, file=SimpleUploadedFile(
                    "z.csv", sample("zlobki-invalid-demo.csv"), content_type="text/csv"))
                res = Resource.raw.get(pk=res.pk)
                report = validate_resource(res)
                self.assertEqual((report["standard"], report["blocking"]), ("zlobki-pl", True))
                stored = ResourceStandardValidation.objects.get(resource_id=res.pk)
                self.assertEqual((stored.standard.code, stored.status), ("zlobki-pl", "invalid"))
                self.assertEqual(Resource.raw.get(pk=res.pk).status, "draft")

                class FakeForm:
                    instance = Resource.raw.get(pk=res.pk)

                bad = SimpleUploadedFile("bad.csv", sample("zlobki-invalid-demo.csv"), content_type="text/csv")
                messages = integration.standard_errors_for_form(FakeForm(), {"status": "published", "dataset": ds, "file": bad})
                self.assertTrue(messages and "Żłobki" in messages[0])
                good = SimpleUploadedFile("ok.csv", sample("zlobki-valid-demo.csv"), content_type="text/csv")
                self.assertEqual(integration.standard_errors_for_form(
                    FakeForm(), {"status": "published", "dataset": ds, "file": good}), [])
                raise _Rollback
        except _Rollback:
            pass


class StandardsApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from mcod.aed.tests.test_integration import _api_client

        cls.client = _api_client()

    def _multipart(self, path, filename, content):
        boundary = "stdboundary"
        body = ("--{b}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{f}\"\r\n"
                "Content-Type: text/csv\r\n\r\n".format(b=boundary, f=filename).encode()
                + content + "\r\n--{b}--\r\n".format(b=boundary).encode())
        return self.client.simulate_post(path, body=body,
                                         headers={"Content-Type": "multipart/form-data; boundary=" + boundary})

    def test_list_schema_files_validate(self):
        resp = self.client.simulate_get("/1.4/standards")
        self.assertEqual(resp.status_code, 200)
        codes = {d["id"] for d in resp.json["data"]}
        self.assertTrue({"aed-pl", "zlobki-pl"} <= codes)
        resp = self.client.simulate_get("/1.4/standards/zlobki-pl/schema")
        self.assertEqual(resp.json["data"]["attributes"]["code"], "zlobki-pl")
        for path in ("schema.xlsx", "schema.csv", "schema.json", "table-schema.json"):
            with self.subTest(path=path):
                self.assertEqual(self.client.simulate_get("/1.4/standards/zlobki-pl/" + path).status_code, 200)
        self.assertEqual(self.client.simulate_get("/1.4/standards/nie-ma/schema").status_code, 404)
        self.assertEqual(self.client.simulate_get("/1.4/standards/zlobki-pl/validate").status_code, 200)
        resp = self._multipart("/1.4/standards/zlobki-pl/validate", "z.csv", sample("zlobki-invalid-demo.csv"))
        attrs = resp.json["data"]["attributes"]
        self.assertEqual((attrs["standard"], attrs["blocking"]), ("zlobki-pl", True))
        resp = self._multipart("/1.4/standards/nie-ma/validate", "z.csv", sample("zlobki-valid-demo.csv"))
        self.assertEqual(resp.status_code, 404)
        resp = self._multipart("/1.4/aed/validate", "a.csv", sample("aed-invalid-demo.csv"))
        self.assertEqual(resp.json["data"]["attributes"]["standard"], "aed-pl")


if __name__ == "__main__":
    unittest.main()


class GenericAggregationTests(unittest.TestCase):
    def test_effective_format(self):
        from mcod.aed.importer import effective_format

        self.assertEqual(effective_format("xlsx", "https://x/download/rejestr_zlobkow_tychy.csv"), "csv")
        self.assertEqual(effective_format("xlsx", "https://x/download/rejestr.rdf"), "rdf")
        self.assertEqual(effective_format("csv", "https://api.dane.gov.pl/resources/1,x/file"), "csv")

    def test_complete_record_and_merge_by_key(self):
        from mcod.aed import merge
        from datetime import date

        s = spec()
        data = generic.complete_record({"nazwa": "Żłobek A", "adres": "ul. Jasna 5, 43-100 Tychy", "liczba_miejsc": 20},
                                       s, 3, "dgp-1", "Urząd Miasta Tychy", date(2026, 11, 22))
        self.assertEqual((data["ulica"], data["nr_budynku"], data["kod_pocztowy"], data["miejscowosc"]),
                         ("ul. Jasna", "5", "43-100", "Tychy"))
        self.assertEqual((data["id_placowki"], data["zrodlo"], data["data_aktualizacji"]),
                         ("dgp-1-3", "Urząd Miasta Tychy", "2026-11-22"))
        town = generic.complete_record({"miejscowosc": "Tychy, miasto"}, s, 1, "k", "n", None)
        self.assertEqual(town["miejscowosc"], "Tychy")

        def rec(resource_id, **d):
            return merge.Rec(resource_id=resource_id, kind="official", source_key="r%d" % resource_id, row_id="1", data=d)

        merged = generic.merge_by_key([
            rec(1, nazwa="Żłobek A", regon="276115858", zrodlo="Gmina", liczba_miejsc=20),
            rec(2, nazwa="ŻŁOBEK A", regon="276115858", zrodlo="GZM", telefon="123"),          # same REGON + name
            rec(3, nazwa="Żłobek B", miejscowosc="Tychy", ulica="ul. Jasna", nr_budynku="5", zrodlo="Gmina"),
            rec(4, nazwa="Żłobek B", miejscowosc="Tychy", ulica="ul. Jasna", nr_budynku="5", zrodlo="GZM"),  # same address
            rec(1, nazwa="Żłobek A", regon="276115858", zrodlo="Gmina"),                          # same resource: never merged
        ], s)
        sizes = sorted(len(group) for _, group in merged)
        self.assertEqual(sizes, [1, 2, 2])
        first = next(d for d, g in merged if len(g) == 2 and d.get("regon"))
        self.assertEqual((first["liczba_miejsc"], first["telefon"], first["zrodlo"]), (20, "123", "Gmina; GZM"))

    def test_generic_run_publishes_nothing_but_builds_objects(self):
        from django.contrib.auth import get_user_model
        from django.core.files.uploadedfile import SimpleUploadedFile

        from mcod.aed import integration
        from mcod.aed.aggregate import run_aggregation
        from mcod.aed.models import AedDevice, DataStandard
        from mcod.aed.standards import load_standard
        from mcod.datasets.models import Dataset
        from mcod.organizations.models import Organization
        from mcod.resources.models import Resource, ResourceFile

        user = get_user_model().objects.filter(is_superuser=True).first()
        with open(os.path.join(STANDARDS_DIR, "zlobki-pl.json"), encoding="utf-8") as fh:
            definition = json.load(fh)
        try:
            with transaction.atomic():
                definition["code"] = "zlobki-t18"
                standard, _ = load_standard(definition)
                for name in ("zlobki-valid-demo.csv", "zlobki-legacy-demo.csv", "zlobki-invalid-demo.csv"):
                    ds = Dataset.objects.create(title="T18 " + name, organization=Organization.objects.first(),
                                                created_by=user, notes="t", status="published")
                    integration.save_dataset_standard(ds, standard, revalidate=False)
                    res = Resource.objects.create(title="T18 " + name, dataset=ds, created_by=user,
                                                  status="published", description="t")
                    ResourceFile.objects.create(resource=res, is_main=True,
                                                file=SimpleUploadedFile(name, sample(name), content_type="text/csv"))
                run = run_aggregation(triggered_by="test", publish=False, standard=DataStandard.objects.get(code="zlobki-t18"))
                self.assertEqual(run.status, "ok")
                by_title = {s["dataset_title"]: s for s in run.report["sources"]}
                self.assertEqual(by_title["T18 zlobki-valid-demo.csv"]["records"], 2)
                self.assertEqual(by_title["T18 zlobki-legacy-demo.csv"]["records"], 2)
                self.assertEqual(by_title["T18 zlobki-invalid-demo.csv"]["records"], 0)  # all rows invalid
                devices = AedDevice.objects.filter(standard__code="zlobki-t18")
                self.assertEqual(devices.count(), 4)
                legacy = next(d for d in devices if d.data.get("miejscowosc") == "Inowrocław")
                self.assertTrue(legacy.id_aed.startswith("PL-ZLOBKI-T18-"))
                self.assertEqual(legacy.data["id_placowki"], legacy.id_aed)
                self.assertEqual(legacy.data["liczba_miejsc"] in (80, 64), True)
                raise _Rollback
        except _Rollback:
            pass

"""Mirroring AED sources into the portal (T12). DB writes are rolled back; no network calls."""
import io
import os
import unittest
from unittest import mock

from django.db import transaction
from openpyxl import Workbook

from mcod.aed import connectors, importer, publishing, validation


class _Rollback(Exception):
    pass


class HelperTests(unittest.TestCase):
    def test_snapshot_specs(self):
        specs = {s.dane_id: s for s in importer.snapshot_specs()}
        self.assertEqual(set(specs), {"4955", "3624", "39512", "4581", "40593"})
        self.assertEqual(specs["39512"].api_link, connectors.WARSAW_AED_ACTION)  # Warsaw = connected API
        self.assertFalse(specs["39512"].content)
        self.assertEqual(specs["4581"].resource_format, "geojson")  # best format chosen
        self.assertTrue(specs["3624"].content.startswith("Długość".encode()) or specs["3624"].content)

    def test_corrected_legionowo_file_passes_and_original_fails(self):
        original = [s for s in importer.snapshot_specs() if s.dane_id == "40593"][0].content
        self.assertTrue(validation.validate_bytes(original, filename="o.csv")["blocking"])
        path = os.path.join(importer.CORRECTED_DIR, importer.CORRECTED_FILES["40593"]["file"])
        with open(path, "rb") as fh:
            fixed = validation.validate_bytes(fh.read(), filename="f.csv")
        self.assertEqual((fixed["blocking"], fixed["rows_invalid"]), (False, 0))

    def test_frequency_and_institution_type(self):
        self.assertEqual(publishing.frequency_code("Codziennie"), "daily")
        self.assertEqual(publishing.frequency_code("Jednorazowe udostępnienie"), "notPlanned")
        self.assertEqual(publishing.frequency_code(None), "irregular")
        self.assertEqual(importer._institution_type("Urząd Miasta Krosna"), "local")
        self.assertEqual(importer._institution_type("Ministerstwo Zdrowia"), "state")

    def test_xlsx_digest_ignores_creation_time(self):
        def book(stamp):
            wb = Workbook()
            wb.properties.created = stamp
            wb.active.append(["a", 1])
            buf = io.BytesIO()
            wb.save(buf)
            return buf.getvalue()

        from datetime import datetime

        one, two = book(datetime(2020, 1, 1)), book(datetime(2021, 1, 1))
        self.assertNotEqual(one, two)
        self.assertEqual(publishing.content_digest(one, "x.xlsx"), publishing.content_digest(two, "x.xlsx"))

    def test_warsaw_connector_requires_token(self):
        with mock.patch.dict(os.environ, {"WARSAW_API_TOKEN": ""}):
            with self.assertRaises(connectors.SourceLoadError):
                connectors.fetch_link(connectors.WARSAW_AED_ACTION)


class ImportTests(unittest.TestCase):
    def test_import_snapshot_is_idempotent_and_sets_standard(self):
        from mcod.aed.models import DatasetStandard
        from mcod.datasets.models import Dataset
        from mcod.resources.models import Resource

        specs = [s for s in importer.snapshot_specs() if s.dane_id in ("3624", "39512", "40593")]
        try:
            with transaction.atomic():
                for spec in specs:  # isolate from the real mirrored datasets
                    spec.dane_id = "test-" + spec.dane_id
                    spec.title = "TEST " + spec.title
                with mock.patch.object(importer, "CORRECTED_FILES", {"test-40593": importer.CORRECTED_FILES["40593"]}):
                    from mcod.aed.standards import ensure_aed_standard

                    standard = ensure_aed_standard()
                    report = importer.ImportReport()
                    for spec in specs:
                        importer.import_spec(spec, standard, report)
                    self.assertEqual(len(report.rows), 4, report.rows)  # 3 sources + corrected Legionowo
                    kinds = sorted(row[4] for row in report.rows)
                    self.assertIn("API", kinds)
                    datasets = Dataset.raw.filter(ext_ident__startswith="dgp-test-")
                    self.assertEqual(datasets.count(), 3)
                    for ds in datasets:
                        self.assertEqual(DatasetStandard.objects.get(dataset=ds).standard.code, "aed-pl")
                    api_res = Resource.raw.get(ext_ident="dgp-res-2512040", dataset__in=datasets)
                    self.assertEqual((api_res.link, api_res.forced_api_type), (connectors.WARSAW_AED_ACTION, True))
                    count = Resource.raw.filter(dataset__in=datasets).count()
                    again = importer.ImportReport()
                    for spec in specs:
                        importer.import_spec(spec, standard, again)
                    self.assertEqual(Resource.raw.filter(dataset__in=datasets).count(), count)
                    self.assertEqual(Dataset.raw.filter(ext_ident__startswith="dgp-test-").count(), 3)
                    self.assertTrue(all(row[5].endswith("unchanged") for row in again.rows), again.rows)
                raise _Rollback
        except _Rollback:
            pass


if __name__ == "__main__":
    unittest.main()

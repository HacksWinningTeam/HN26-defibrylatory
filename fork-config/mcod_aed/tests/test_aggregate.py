"""Aggregation into the common dataset (T13). Isolated test standard, rolled-back transaction, no network."""
import csv
import io
import json
import os
import unittest

from django.db import transaction

from mcod.aed import exports, merge
from mcod.aed.schema import FIELD_NAMES

SAMPLES = os.path.join(os.path.dirname(__file__), "samples")


class _Rollback(Exception):
    pass


def rec(resource_id, lat, lon, kind="official", name="AED", **data):
    data.setdefault("nazwa", name)
    return merge.Rec(resource_id=resource_id, kind=kind, source_key="r{}".format(resource_id),
                     row_id=str(lat), data=data, lat=lat, lon=lon)


class MergeTests(unittest.TestCase):
    def test_official_and_osm_within_25m_merge_official_first(self):
        result = merge.merge([
            rec(2, 52.20863, 21.01488, kind="osm", name="AED – Urząd", godziny_dostepnosci="24/7", zrodlo="OpenStreetMap"),
            rec(1, 52.20862, 21.01487, name="Urząd Dzielnicy Mokotów", zrodlo="Urząd m.st. Warszawy"),
        ])
        self.assertEqual(len(result), 1)
        _, _, _, data, group = result[0]
        self.assertEqual(data["nazwa"], "Urząd Dzielnicy Mokotów")  # official wins
        self.assertEqual(data["godziny_dostepnosci"], "24/7")  # missing field filled from OSM
        self.assertEqual(data["zrodlo"], "Urząd m.st. Warszawy; OpenStreetMap")
        self.assertEqual(len(group), 2)
        self.assertTrue(data["id_aed"].startswith("PL-AED-"))

    def test_same_resource_never_merged_and_far_points_separate(self):
        result = merge.merge([rec(1, 52.2, 21.0), rec(1, 52.20001, 21.0), rec(2, 52.3, 21.0)])
        self.assertEqual(len(result), 3)

    def test_loose_distance_needs_similar_name(self):
        same = merge.merge([rec(1, 52.2, 21.0, name="Szkoła Podstawowa nr 1"),
                            rec(2, 52.2005, 21.0, name="Szkoła Podstawowa nr 1")])  # ~55 m
        other = merge.merge([rec(1, 52.2, 21.0, name="Szkoła Podstawowa nr 1"),
                             rec(2, 52.2005, 21.0, name="Apteka Centrum")])
        self.assertEqual((len(same), len(other)), (1, 2))

    def test_invalid_records_skipped_and_outliers_flagged(self):
        recs = [rec(1, 52.2, 21.0), rec(1, 52.21, 21.0), rec(1, 52.22, 21.0), rec(1, 50.0, 19.9)]
        merge.flag_coordinate_problems(recs)
        self.assertFalse(recs[3].valid)
        self.assertIn("wspolrzedne_daleko_od_pozostalych", recs[3].flags)
        self.assertEqual(len(merge.merge(recs)), 3)


class ExportTests(unittest.TestCase):
    def test_csv_and_geojson(self):
        from mcod.aed.models import AedDevice

        devices = [AedDevice(id_aed="PL-AED-1", lat=52.2, lon=21.0,
                             data={"id_aed": "PL-AED-1", "nazwa": "A", "w_budynku": True, "miejscowosc": "W"})]
        rows = list(csv.reader(io.StringIO(exports.csv_bytes(devices).decode())))
        self.assertEqual(rows[0], list(FIELD_NAMES))
        self.assertEqual(rows[1][FIELD_NAMES.index("w_budynku")], "true")
        geo = json.loads(exports.geojson_bytes(devices, {"x": 1}).decode())
        self.assertEqual(geo["features"][0]["geometry"]["coordinates"], [21.0, 52.2])

    def test_device_feature_contract(self):
        from mcod.aed.models import AedDevice
        from mcod.aed.views import device_feature

        device = AedDevice(id_aed="PL-AED-1", lat=52.2, lon=21.0, sources=[{"nazwa": "X", "typ": "osm", "url": "u", "dataset_id": 1}],
                           data={"nazwa": "A", "cecha_ulicy": "ul.", "nazwa_ulicy": "Jasna", "nr_budynku": "5",
                                 "kod_pocztowy": "38-400", "miejscowosc": "Krosno"})
        props = device_feature(device)["properties"]
        self.assertEqual(set(props), {"id_aed", "nazwa", "adres", "miejscowosc", "opis_lokalizacji", "w_budynku", "pietro",
                                      "dostep", "godziny_dostepnosci", "zabezpieczenie", "status", "dysponent",
                                      "telefon_kontaktowy", "data_aktualizacji", "zrodla"})
        self.assertEqual(props["adres"], "ul. Jasna 5, 38-400 Krosno")
        self.assertIsNone(props["pietro"])
        self.assertEqual(props["zrodla"], [{"nazwa": "X", "typ": "osm", "url": "u"}])


class AggregationRunTests(unittest.TestCase):
    def test_run_aggregates_only_non_blocked_resources_of_the_standard(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        from mcod.aed import integration
        from mcod.aed.aggregate import run_aggregation
        from mcod.aed.models import AedDevice, AedSourceRecord, DataStandard
        from mcod.aed.resource_validation import validate_resource
        from mcod.datasets.models import Dataset
        from mcod.organizations.models import Organization
        from mcod.resources.models import Resource, ResourceFile
        from django.contrib.auth import get_user_model

        user = get_user_model().objects.filter(is_superuser=True).first()
        org = Organization.objects.first()

        def dataset_with(name, sample, standard):
            ds = Dataset.objects.create(title="T13 " + name, organization=org, created_by=user, notes="t", status="published")
            integration.save_dataset_standard(ds, standard, revalidate=False)
            res = Resource.objects.create(title="T13 " + name, dataset=ds, created_by=user, status="published", description="t")
            with open(os.path.join(SAMPLES, sample), "rb") as fh:
                ResourceFile.objects.create(resource=res, is_main=True, file=SimpleUploadedFile(sample, fh.read(), content_type="text/csv"))
            return Resource.raw.get(pk=res.pk)

        try:
            with transaction.atomic():
                standard = DataStandard.objects.create(code="t13-test", name="T13 test", version="1", json_schema={})
                good = dataset_with("Bydgoszcz", "aed-bydgoszcz-demo.csv", standard)
                other = dataset_with("Toruń", "aed-torun-demo.csv", standard)
                bad = dataset_with("bad", "aed-invalid-demo.csv", standard)
                self.assertTrue(validate_resource(bad)["blocking"])  # -> draft, excluded
                run = run_aggregation(triggered_by="test", publish=False, standard=standard)
                self.assertEqual(run.status, "ok")
                sources = {s["resource_id"]: s for s in run.report["sources"]}
                self.assertEqual(set(sources), {good.pk, other.pk})
                self.assertEqual(run.devices_count, 5)
                devices = AedDevice.objects.filter(standard=standard)
                self.assertEqual(devices.count(), 5)
                self.assertTrue(all(d.sources and d.sources[0]["dataset_id"] in (good.dataset_id, other.dataset_id) for d in devices))
                self.assertEqual(AedSourceRecord.objects.filter(resource_id__in=[good.pk, other.pk]).count(), 5)
                again = run_aggregation(triggered_by="test", publish=False, standard=standard)
                self.assertEqual(AedDevice.objects.filter(standard=standard).count(), 5)  # rebuilt, not duplicated
                self.assertEqual(again.devices_count, 5)
                raise _Rollback
        except _Rollback:
            pass


class CommonApiTests(unittest.TestCase):
    def test_devices_and_sources_endpoints(self):
        from mcod.aed.tests.test_integration import _api_client

        client = _api_client()
        resp = client.simulate_get("/1.4/aed/devices", params={"q": "krosno"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.headers["content-type"].startswith("application/geo+json"))
        body = json.loads(resp.text)
        self.assertEqual(body["type"], "FeatureCollection")
        self.assertEqual(body["meta"]["count"], len(body["features"]))
        self.assertEqual(client.simulate_get("/1.4/aed/devices", params={"bbox": "x"}).status_code, 400)
        resp = client.simulate_get("/1.4/aed/sources")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(set(resp.json), {"jsonapi", "links", "meta", "data"})
        self.assertIn("aed_count", resp.json["meta"])


if __name__ == "__main__":
    unittest.main()

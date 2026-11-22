"""API routes, dataset API attribute and dataset admin hook (run against the live fork DB,
every write inside a rolled-back transaction)."""
import json
import unittest

from django.db import transaction
from falcon import testing


class _Rollback(Exception):
    pass


def _api_client():
    from mcod.aed import integration

    integration.register_routes()
    integration.patch_dataset_api()
    from mcod.api import get_api_app

    return testing.TestClient(get_api_app())


class SchemaApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = _api_client()

    def test_schema_envelope_like_upstream(self):
        resp = self.client.simulate_get("/1.4/aed/schema")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.headers["content-type"].startswith("application/vnd.api+json"))
        body = resp.json
        self.assertEqual(set(body), {"jsonapi", "links", "meta", "data"})
        self.assertEqual(body["jsonapi"], {"version": "1.4"})
        self.assertEqual(
            set(body["meta"]), {"path", "language", "server_time", "relative_uri", "params"}
        )
        data = body["data"]
        self.assertEqual((data["type"], data["id"]), ("aed_schema", "aed-pl"))
        self.assertEqual(data["attributes"]["fields_count"], 42)
        self.assertEqual(len(data["attributes"]["groups"]), 6)
        self.assertIn("json_schema", data["attributes"]["downloads"])

    def test_unversioned_path_also_works(self):
        self.assertEqual(self.client.simulate_get("/aed/schema").status_code, 200)

    def test_downloads(self):
        cases = {
            "/1.4/aed/schema.xlsx": "application/vnd.openxmlformats",
            "/1.4/aed/schema.csv": "text/csv",
            "/1.4/aed/schema.json": "application/schema+json",
            "/1.4/aed/table-schema.json": "application/json",
        }
        for path, content_type in cases.items():
            with self.subTest(path=path):
                resp = self.client.simulate_get(path)
                self.assertEqual(resp.status_code, 200)
                self.assertTrue(resp.headers["content-type"].startswith(content_type))
                self.assertIn("attachment", resp.headers["content-disposition"])
        js = json.loads(self.client.simulate_get("/1.4/aed/schema.json").text)
        self.assertIn("nazwa", js["properties"])


class DataStandardTests(unittest.TestCase):
    def test_aed_standard_seeded(self):
        from mcod.aed.models import DataStandard

        standard = DataStandard.objects.get(code="aed-pl")
        self.assertEqual(standard.version, "1.0.0")
        self.assertEqual(standard.max_invalid_ratio, 0.2)
        self.assertIn("properties", standard.json_schema)

    def test_dataset_api_attribute_and_admin_save(self):
        from mcod.aed import integration
        from mcod.aed.models import DatasetStandard, DataStandard
        from mcod.datasets.models import Dataset

        dataset = Dataset.objects.order_by("id").first()
        if dataset is None:
            self.skipTest("no dataset in the fork DB")
        standard = DataStandard.objects.get(code="aed-pl")
        try:
            with transaction.atomic():
                DatasetStandard.objects.filter(dataset_id=dataset.pk).delete()
                self.assertIsNone(integration.data_standard_for(dataset))
                integration.save_dataset_standard(dataset, standard)
                expected = {"code": "aed-pl", "name": standard.name, "version": "1.0.0"}
                self.assertEqual(integration.data_standard_for(dataset), expected)
                self.assertEqual(integration.data_standard_for({"id": dataset.pk}), expected)
                integration.save_dataset_standard(dataset, None)
                self.assertFalse(DatasetStandard.objects.filter(dataset_id=dataset.pk).exists())
                raise _Rollback
        except _Rollback:
            pass

    def test_dataset_admin_form_has_standard_field(self):
        from django.contrib.auth import get_user_model
        from django.test import RequestFactory

        from mcod.aed import integration
        from mcod.datasets import admin as dataset_admin
        from mcod.datasets.models import Dataset

        integration.patch_dataset_admin()
        user = get_user_model().objects.filter(is_superuser=True).first()
        dataset = Dataset.objects.order_by("id").first()
        if user is None or dataset is None:
            self.skipTest("fixture admin/dataset missing")
        request = RequestFactory().get("/")
        request.user = user
        from django.contrib import admin

        model_admin = admin.site._registry[Dataset]
        self.assertIsInstance(model_admin, dataset_admin.DatasetAdminMixin)
        fieldsets = model_admin.get_fieldsets(request, dataset)
        general = [opts for _, opts in fieldsets if "suit-tab-general" in opts.get("classes", ())][0]
        self.assertIn("data_standard", general["fields"])
        form_class = model_admin.get_form(request, dataset)
        self.assertIn("data_standard", form_class.base_fields)


if __name__ == "__main__":
    unittest.main()

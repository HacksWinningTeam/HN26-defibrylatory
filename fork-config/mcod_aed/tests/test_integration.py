"""API routes, dataset API attribute and dataset admin hook (run against the live fork DB,
every write inside a rolled-back transaction)."""
import json
import os
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


class ValidateApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = _api_client()
        here = os.path.join(os.path.dirname(__file__), "samples")
        cls.valid = open(os.path.join(here, "aed-bydgoszcz-demo.csv"), "rb").read()
        cls.invalid = open(os.path.join(here, "aed-invalid-demo.csv"), "rb").read()

    def _multipart(self, filename, content):
        boundary = "aedboundary"
        body = (
            "--{b}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{f}\"\r\n"
            "Content-Type: text/csv\r\n\r\n".format(b=boundary, f=filename).encode()
            + content + "\r\n--{b}--\r\n".format(b=boundary).encode()
        )
        return self.client.simulate_post(
            "/1.4/aed/validate", body=body,
            headers={"Content-Type": "multipart/form-data; boundary=" + boundary},
        )

    def test_help(self):
        resp = self.client.simulate_get("/1.4/aed/validate")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["data"]["type"], "aed_validation_help")

    def test_multipart_valid_and_invalid(self):
        resp = self._multipart("ok.csv", self.valid)
        self.assertEqual(resp.status_code, 200)
        body = resp.json
        self.assertEqual(set(body), {"jsonapi", "links", "meta", "data"})
        attrs = body["data"]["attributes"]
        self.assertEqual(body["data"]["type"], "aed_validation")
        self.assertEqual((attrs["valid"], attrs["blocking"], attrs["source"]["type"]), (True, False, "upload"))
        resp = self._multipart("bad.csv", self.invalid)
        self.assertEqual(resp.status_code, 200)
        attrs = resp.json["data"]["attributes"]
        self.assertEqual((attrs["valid"], attrs["blocking"], attrs["rows_invalid"]), (False, True, 3))

    def test_raw_body_and_strict_param(self):
        resp = self.client.simulate_post("/1.4/aed/validate", body=self.valid, headers={"Content-Type": "text/csv"})
        self.assertEqual(resp.json["data"]["attributes"]["status"], "valid")
        resp = self.client.simulate_post("/1.4/aed/validate", body=self.valid,
                                         headers={"Content-Type": "text/csv"}, params={"strict": "true"})
        self.assertTrue(resp.json["data"]["attributes"]["strict"])

    def test_errors(self):
        resp = self.client.simulate_post("/1.4/aed/validate", body=b"", headers={"Content-Type": "text/csv"})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("errors", resp.json)
        resp = self.client.simulate_post("/1.4/aed/validate", json={"resource_id": 99999999})
        self.assertEqual(resp.status_code, 404)
        resp = self.client.simulate_get("/1.4/resources/99999999/standard-validation")
        self.assertEqual(resp.status_code, 404)


class AutomaticValidationTests(unittest.TestCase):
    """Stored validation + blocking + admin form rule, inside a rolled-back transaction."""

    def _make_dataset_resource(self, content):
        from django.contrib.auth import get_user_model
        from django.core.files.uploadedfile import SimpleUploadedFile

        from mcod.aed import integration
        from mcod.aed.models import DataStandard
        from mcod.datasets.models import Dataset
        from mcod.organizations.models import Organization
        from mcod.resources.models import Resource, ResourceFile

        user = get_user_model().objects.filter(is_superuser=True).first()
        org = Organization.objects.first()
        dataset = Dataset.objects.create(title="T14 test dataset", organization=org, created_by=user,
                                         notes="test", status="published")
        integration.save_dataset_standard(dataset, DataStandard.objects.get(code="aed-pl"), revalidate=False)
        resource = Resource.objects.create(title="T14 test", dataset=dataset, created_by=user, status="published",
                                           description="test")
        ResourceFile.objects.create(resource=resource, is_main=True,
                                    file=SimpleUploadedFile("t.csv", content, content_type="text/csv"))
        return dataset, Resource.raw.get(pk=resource.pk)

    def test_validate_resource_blocks_and_form_refuses_republish(self):
        from mcod.aed import integration
        from mcod.aed.models import ResourceStandardValidation
        from mcod.aed.resource_validation import validate_resource
        from mcod.resources.models import Resource

        here = os.path.join(os.path.dirname(__file__), "samples")
        bad = open(os.path.join(here, "aed-invalid-demo.csv"), "rb").read()
        good = open(os.path.join(here, "aed-torun-demo.csv"), "rb").read()
        try:
            with transaction.atomic():
                _, resource = self._make_dataset_resource(bad)
                report = validate_resource(resource)
                self.assertTrue(report["blocking"])
                stored = ResourceStandardValidation.objects.get(resource_id=resource.pk)
                self.assertEqual((stored.status, stored.blocking), ("invalid", True))
                self.assertEqual(Resource.raw.get(pk=resource.pk).status, "draft")

                class FakeForm:
                    instance = Resource.raw.get(pk=resource.pk)
                messages = integration.standard_errors_for_form(FakeForm(), {"status": "published",
                                                                            "dataset": resource.dataset})
                self.assertTrue(messages and "nie można opublikować" in messages[0])
                self.assertEqual(integration.standard_errors_for_form(FakeForm(), {"status": "draft"}), [])

                from django.core.files.uploadedfile import SimpleUploadedFile

                ok_upload = SimpleUploadedFile("ok.csv", good, content_type="text/csv")
                self.assertEqual(integration.standard_errors_for_form(
                    FakeForm(), {"status": "published", "dataset": resource.dataset, "file": ok_upload}), [])
                bad_upload = SimpleUploadedFile("bad.csv", bad, content_type="text/csv")
                self.assertTrue(integration.standard_errors_for_form(
                    FakeForm(), {"status": "published", "dataset": resource.dataset, "file": bad_upload}))
                raise _Rollback
        except _Rollback:
            pass

    def test_valid_resource_stays_published(self):
        from mcod.aed.resource_validation import validate_resource
        from mcod.resources.models import Resource

        here = os.path.join(os.path.dirname(__file__), "samples")
        good = open(os.path.join(here, "aed-torun-demo.csv"), "rb").read()
        try:
            with transaction.atomic():
                _, resource = self._make_dataset_resource(good)
                report = validate_resource(resource)
                self.assertEqual((report["status"], report["blocking"]), ("valid", False))
                self.assertEqual(Resource.raw.get(pk=resource.pk).status, "published")
                raise _Rollback
        except _Rollback:
            pass

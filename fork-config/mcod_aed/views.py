"""Falcon views of `mcod.aed` (registered under /1.4 by `integration.register_routes`)."""
import falcon

from mcod.aed import jsonapi, schema, schema_export
from mcod.aed.standards import AED_STANDARD_CODE


def _api_root(req):
    return "{}://{}".format(req.scheme, req.netloc)


def _schema_attributes(req):
    doc = schema_export.schema_document()
    root = _api_root(req)
    doc["downloads"] = {
        "xlsx": root + "/1.4/aed/schema.xlsx",
        "csv_template": root + "/1.4/aed/schema.csv",
        "json_schema": root + "/1.4/aed/schema.json",
        "table_schema": root + "/1.4/aed/table-schema.json",
    }
    doc["fields_count"] = len(schema.FIELDS)
    return doc


class AedSchemaView:
    """GET /1.4/aed/schema — the standard AED structure (DEC-014)."""

    def on_get(self, req, resp, **kwargs):
        data = jsonapi.resource_object(
            "aed_schema",
            AED_STANDARD_CODE,
            _schema_attributes(req),
            self_link=_api_root(req) + "/1.4/aed/schema",
        )
        jsonapi.send(resp, req, data)


class AedSchemaFileView:
    """GET /1.4/aed/schema.{xlsx,csv,json} and /1.4/aed/table-schema.json — downloads."""

    def __init__(self, kind):
        self.kind = kind

    def on_get(self, req, resp, **kwargs):
        version = schema.SCHEMA_VERSION
        if self.kind == "xlsx":
            body = schema_export.xlsx_bytes()
            content_type = schema_export.XLSX_CONTENT_TYPE
            filename = "aed-schema-{}.xlsx".format(version)
        elif self.kind == "csv":
            body = schema_export.csv_template().encode("utf-8-sig")
            content_type = "text/csv; charset=utf-8"
            filename = "aed-template-{}.csv".format(version)
        elif self.kind == "json":
            import json

            body = json.dumps(schema_export.json_schema(), ensure_ascii=False, indent=2).encode("utf-8")
            content_type = "application/schema+json"
            filename = "aed-schema-{}.json".format(version)
        elif self.kind == "table":
            import json

            body = json.dumps(schema_export.table_schema(), ensure_ascii=False, indent=2).encode("utf-8")
            content_type = "application/json"
            filename = "aed-table-schema-{}.json".format(version)
        else:  # pragma: no cover - routes only use the kinds above
            raise falcon.HTTPNotFound()
        resp.status = falcon.HTTP_200
        resp.content_type = content_type
        resp.data = body
        resp.set_header("Content-Disposition", 'attachment; filename="{}"'.format(filename))


ROUTES = [
    ("/aed/schema", AedSchemaView()),
    ("/aed/schema.xlsx", AedSchemaFileView("xlsx")),
    ("/aed/schema.csv", AedSchemaFileView("csv")),
    ("/aed/schema.json", AedSchemaFileView("json")),
    ("/aed/table-schema.json", AedSchemaFileView("table")),
]

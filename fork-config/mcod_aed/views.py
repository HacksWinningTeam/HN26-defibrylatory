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


# --- Validation (T14) ------------------------------------------------------------------------

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
TRUE_PARAMS = {"1", "true", "tak", "yes"}


def _validation_help(req):
    root = _api_root(req)
    return {
        "description": (
            "Walidacja danych o defibrylatorach AED względem wzorcowego zakresu danych (standard aed-pl). "
            "Wyślij plik (multipart/form-data, pole 'file'), surową treść pliku (Content-Type text/csv, "
            "application/json, ...), albo JSON {\"url\": \"...\"} lub {\"resource_id\": 123}."
        ),
        "methods": {
            "POST multipart": "curl -F file=@dane.csv {}/1.4/aed/validate".format(root),
            "POST url": "curl -H 'Content-Type: application/json' -d '{{\"url\": \"https://...\"}}' {}/1.4/aed/validate".format(root),
            "POST resource_id": "curl -H 'Content-Type: application/json' -d '{{\"resource_id\": 123}}' {}/1.4/aed/validate".format(root),
        },
        "parameters": {
            "strict": "true = każda brakująca wymagana kolumna jest błędem (pełna zgodność ze standardem)",
            "format": "csv | xlsx | json | geojson | xml (domyślnie wykrywany automatycznie)",
        },
        "formats": ["csv", "xlsx", "json", "geojson", "xml"],
        "limits": {"max_upload_mb": MAX_UPLOAD_BYTES // 1024 // 1024, "errors_listed": 500},
        "schema": root + "/1.4/aed/schema",
        "template_csv": root + "/1.4/aed/schema.csv",
    }


def _error(resp, req, status, code, title, detail):
    jsonapi.send_errors(resp, req, status, [{"code": code, "title": title, "detail": detail}])


def _read_request_input(req):
    """-> dict(raw|url|resource_id, filename, fmt)."""
    content_type = (req.content_type or "").lower()
    if req.content_length and req.content_length > MAX_UPLOAD_BYTES + 1024 * 64:
        raise falcon.HTTPPayloadTooLarge(
            title="413 Payload Too Large",
            description="Maksymalny rozmiar danych: {} MB.".format(MAX_UPLOAD_BYTES // 1024 // 1024),
        )
    if content_type.startswith("multipart/form-data"):
        form = req.get_media()
        result = {}
        for part in form:
            if part.name == "file":
                result["raw"] = part.stream.read(MAX_UPLOAD_BYTES + 1)
                result["filename"] = part.secure_filename if part.filename else None
            elif part.name in ("url", "resource_id", "format", "strict"):
                result[part.name] = part.text
        return result
    if content_type.startswith("application/json") or content_type.startswith(jsonapi.JSONAPI_CONTENT_TYPE):
        raw = req.bounded_stream.read(MAX_UPLOAD_BYTES + 1)
        import json

        try:
            body = json.loads(raw.decode("utf-8")) if raw else {}
        except (ValueError, UnicodeDecodeError):
            body = None
        if isinstance(body, dict) and isinstance(body.get("data"), dict) and "attributes" in body["data"]:
            body = body["data"]["attributes"]  # JSON:API style request
        if isinstance(body, dict) and ("url" in body or "resource_id" in body):
            return {k: body[k] for k in ("url", "resource_id", "format", "strict") if k in body}
        return {"raw": raw, "filename": None, "fmt": "geojson" if b"FeatureCollection" in raw[:20000] else "json"}
    raw = req.bounded_stream.read(MAX_UPLOAD_BYTES + 1)
    fmt = None
    if "csv" in content_type or "text/plain" in content_type:
        fmt = "csv"
    elif "spreadsheetml" in content_type or "excel" in content_type:
        fmt = "xlsx"
    elif "xml" in content_type:
        fmt = "xml"
    return {"raw": raw, "filename": None, "fmt": fmt}


class AedValidateView:
    """POST /1.4/aed/validate — validate data against the AED standard (T14). GET = usage."""

    def on_get(self, req, resp, **kwargs):
        data = jsonapi.resource_object("aed_validation_help", "aed-pl", _validation_help(req))
        jsonapi.send(resp, req, data)

    def on_post(self, req, resp, **kwargs):
        from mcod.aed import connectors, validation
        from mcod.aed.models import DataStandard

        try:
            payload = _read_request_input(req)
        except falcon.HTTPPayloadTooLarge:
            raise
        except Exception as exc:  # malformed multipart etc.
            return _error(resp, req, falcon.HTTP_400, "400_bad_request", "400 Bad Request",
                          "Nie można odczytać żądania: {}".format(exc))
        strict = str(req.get_param("strict") or payload.get("strict") or "").lower() in TRUE_PARAMS
        fmt = req.get_param("format") or payload.get("format") or payload.get("fmt")
        standard = DataStandard.objects.filter(code=AED_STANDARD_CODE).first()
        max_ratio = standard.max_invalid_ratio if standard else validation.DEFAULT_MAX_INVALID_RATIO
        source = {}
        try:
            if payload.get("resource_id") not in (None, ""):
                from mcod.resources.models import Resource

                resource = Resource.raw.filter(pk=int(payload["resource_id"]), is_removed=False).first()
                if resource is None:
                    return _error(resp, req, falcon.HTTP_404, "404_not_found", "404 Not Found",
                                  "Nie ma zasobu o id {}.".format(payload["resource_id"]))
                raw, filename, resource_fmt = connectors.resource_bytes(resource)
                fmt = fmt or resource_fmt
                source = {"type": "resource", "resource_id": resource.pk, "dataset_id": resource.dataset_id,
                          "title": resource.title}
            elif payload.get("url"):
                raw, filename = connectors.fetch_url(str(payload["url"]), max_bytes=MAX_UPLOAD_BYTES)
                source = {"type": "url", "url": str(payload["url"])}
            else:
                raw, filename = payload.get("raw") or b"", payload.get("filename")
                source = {"type": "upload", "filename": filename}
            if len(raw) > MAX_UPLOAD_BYTES:
                return _error(resp, req, falcon.HTTP_413, "413_payload_too_large", "413 Payload Too Large",
                              "Maksymalny rozmiar danych: {} MB.".format(MAX_UPLOAD_BYTES // 1024 // 1024))
            report = validation.validate_bytes(raw, filename=filename, fmt=fmt, strict=strict,
                                               max_invalid_ratio=max_ratio)
        except (ValueError, TypeError) as exc:
            if not isinstance(exc, validation.ValidationInputError):
                return _error(resp, req, falcon.HTTP_400, "400_bad_request", "400 Bad Request", str(exc))
            return _error(resp, req, falcon.HTTP_400, "400_unreadable_data", "400 Bad Request", str(exc))
        except connectors.SourceLoadError as exc:
            return _error(resp, req, falcon.HTTP_400, "400_source_unavailable", "400 Bad Request", str(exc))
        report["source"] = source
        data = jsonapi.resource_object("aed_validation", validation.new_report_id(), report)
        jsonapi.send(resp, req, data)


class ResourceStandardValidationView:
    """GET /1.4/resources/{id}/standard-validation — stored automatic validation of a resource."""

    def on_get(self, req, resp, id=None, **kwargs):
        from mcod.aed.models import ResourceStandardValidation

        obj = ResourceStandardValidation.objects.select_related("standard").filter(resource_id=id).first()
        if obj is None:
            return _error(resp, req, falcon.HTTP_404, "404_not_found", "404 Not Found",
                          "Zasób {} nie był walidowany względem standardu danych (jego zbiór nie ma "
                          "ustawionego pola „Standard danych”).".format(id))
        root = _api_root(req)
        data = jsonapi.resource_object(
            "resource_standard_validation", obj.resource_id, obj.as_api_attributes(),
            self_link="{}/1.4/resources/{}/standard-validation".format(root, obj.resource_id),
            relationships={"resource": {"data": {"type": "resource", "id": str(obj.resource_id)},
                                        "links": {"related": "{}/1.4/resources/{}".format(root, obj.resource_id)}}},
        )
        jsonapi.send(resp, req, data)


ROUTES += [
    ("/aed/validate", AedValidateView()),
    ("/resources/{id:int}/standard-validation", ResourceStandardValidationView()),
]

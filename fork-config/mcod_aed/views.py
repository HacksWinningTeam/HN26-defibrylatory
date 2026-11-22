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
    """POST /1.4/aed/validate and /1.4/standards/{code}/validate — validate data against a standard (T14/T17).
    GET = usage."""

    def on_get(self, req, resp, **kwargs):
        code = kwargs.get("code") or AED_STANDARD_CODE
        help_doc = _validation_help(req)
        if code != AED_STANDARD_CODE:
            root = _api_root(req)
            path = "{}/1.4/standards/{}".format(root, code)
            help_doc["description"] = help_doc["description"].replace("o defibrylatorach AED", "").replace(
                "(standard aed-pl)", "(standard {})".format(code))
            help_doc["methods"] = {k: v.replace(root + "/1.4/aed/validate", path + "/validate")
                                   for k, v in help_doc["methods"].items()}
            help_doc["schema"] = path + "/schema"
            help_doc["template_csv"] = path + "/schema.csv"
        help_type = "aed_validation_help" if code == AED_STANDARD_CODE else "validation_help"  # AED API unchanged
        data = jsonapi.resource_object(help_type, code, help_doc)
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
        code = kwargs.get("code") or AED_STANDARD_CODE
        standard = DataStandard.objects.filter(code=code, is_active=True).first()
        if standard is None and code != AED_STANDARD_CODE:
            return _error(resp, req, falcon.HTTP_404, "404_not_found", "404 Not Found",
                          "Nie ma aktywnego standardu danych „{}”.".format(code))
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
            report = validation.validate_for_standard(raw, standard=standard, filename=filename, fmt=fmt,
                                                      strict=strict)
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


# --- Common dataset (T13) --------------------------------------------------------------------

DEVICE_PROPERTIES = (
    "id_aed", "nazwa", "adres", "miejscowosc", "opis_lokalizacji", "w_budynku", "pietro", "dostep",
    "godziny_dostepnosci", "zabezpieczenie", "status", "dysponent", "telefon_kontaktowy", "data_aktualizacji",
)
_devices_cache = {}


def _address(data):
    street = " ".join(str(p) for p in (data.get("cecha_ulicy"), data.get("nazwa_ulicy")) if p)
    number = data.get("nr_budynku") or ""
    if number and data.get("nr_lokalu"):
        number = "{}/{}".format(number, data["nr_lokalu"])
    line1 = " ".join(p for p in (street, number) if p)
    line2 = " ".join(str(p) for p in (data.get("kod_pocztowy"), data.get("miejscowosc")) if p)
    if not street:
        return None
    return ", ".join(p for p in (line1, line2) if p) or None


def device_feature(device):
    data = device.data
    props = {}
    for name in DEVICE_PROPERTIES:
        value = _address(data) if name == "adres" else data.get(name)
        props[name] = None if value in ("", None) else value
    props["id_aed"] = device.id_aed
    props["zrodla"] = [{k: s.get(k) for k in ("nazwa", "typ", "url")} for s in (device.sources or [])]
    return {
        "type": "Feature",
        "id": device.id_aed,
        "geometry": {"type": "Point", "coordinates": [device.lon, device.lat]},
        "properties": props,
    }


def _latest_run():
    from mcod.aed.models import AedImportRun

    return AedImportRun.objects.filter(status=AedImportRun.STATUS_OK).order_by("-pk").first()


class AedDevicesView:
    """GET /1.4/aed/devices[?bbox=minLon,minLat,maxLon,maxLat&q=] — common dataset as GeoJSON (map)."""

    def on_get(self, req, resp, **kwargs):
        import json

        from mcod.aed.models import AedDevice
        from mcod.aed.exports import LICENSE

        run = _latest_run()
        bbox_param = req.get_param("bbox")
        query = (req.get_param("q") or "").strip().lower()
        cache_key = (run.pk if run else 0, bbox_param, query)
        body = _devices_cache.get(cache_key)
        if body is None:
            qs = AedDevice.objects.order_by("id_aed")
            if bbox_param:
                try:
                    min_lon, min_lat, max_lon, max_lat = [float(v) for v in bbox_param.split(",")]
                except ValueError:
                    return _error(resp, req, falcon.HTTP_400, "400_bad_request", "400 Bad Request",
                                  "bbox = minLon,minLat,maxLon,maxLat")
                qs = qs.filter(lon__gte=min_lon, lon__lte=max_lon, lat__gte=min_lat, lat__lte=max_lat)
            features = [device_feature(d) for d in qs.iterator()]
            if query:
                features = [f for f in features if query in " ".join(
                    str(f["properties"].get(k) or "") for k in ("nazwa", "adres", "miejscowosc", "opis_lokalizacji")).lower()]
            body = json.dumps({
                "type": "FeatureCollection",
                "meta": {
                    "count": len(features),
                    "generated_at": run.finished_at.strftime("%Y-%m-%dT%H:%M:%SZ") if run and run.finished_at else None,
                    "license": LICENSE,
                    "standard": "aed-pl",
                },
                "features": features,
            }, ensure_ascii=False).encode("utf-8")
            if len(_devices_cache) > 20:
                _devices_cache.clear()
            _devices_cache[cache_key] = body
        resp.status = falcon.HTTP_200
        resp.content_type = "application/geo+json; charset=utf-8"
        resp.data = body


class AedSourcesView:
    """GET /1.4/aed/sources — datasets aggregated into the common dataset, with coverage (last run)."""

    def on_get(self, req, resp, **kwargs):
        from mcod.aed.models import AedDevice

        run = _latest_run()
        root = _api_root(req)
        if run is None:
            jsonapi.send(resp, req, [], count=0, aed_count=AedDevice.objects.count(), updated_at=None)
            return
        report = run.report
        data = []
        for entry in report.get("sources", []):
            attrs = dict(entry)
            attrs["title"] = entry["dataset_title"]
            attrs["record_count"] = entry.get("records", 0)
            data.append(jsonapi.resource_object(
                "aed_source", entry["resource_id"], attrs,
                self_link="{}/1.4/resources/{}".format(root, entry["resource_id"]),
                relationships={"dataset": {"data": {"type": "dataset", "id": str(entry["dataset_id"])},
                                           "links": {"related": "{}/1.4/datasets/{}".format(root, entry["dataset_id"])}}},
            ))
        jsonapi.send(
            resp, req, data,
            count=len(data),
            aed_count=report.get("devices", 0),
            multi_source_aed_count=report.get("multi_source_devices", 0),
            record_count=report.get("records", 0),
            records_included=report.get("records_included", 0),
            updated_at=run.finished_at.strftime("%Y-%m-%dT%H:%M:%SZ") if run.finished_at else None,
            run_id=run.pk,
            standard=report.get("standard"),
            national_dataset=report.get("national_dataset"),
        )


ROUTES += [
    ("/aed/devices", AedDevicesView()),
    ("/aed/sources", AedSourcesView()),
]


# --- Data-defined standards (T17, DEC-019) ---------------------------------------------------------


def _standard_or_404(req, resp, code):
    from mcod.aed.models import DataStandard

    standard = DataStandard.objects.filter(code=code, is_active=True).first()
    if standard is None:
        _error(resp, req, falcon.HTTP_404, "404_not_found", "404 Not Found",
               "Nie ma aktywnego standardu danych „{}”.".format(code))
    return standard


def _standard_links(req, code):
    base = "{}/1.4/standards/{}".format(_api_root(req), code)
    return {"schema": base + "/schema", "xlsx": base + "/schema.xlsx", "csv_template": base + "/schema.csv",
            "json_schema": base + "/schema.json", "table_schema": base + "/table-schema.json",
            "validate": base + "/validate", "sources": base + "/sources"}


class StandardsListView:
    """GET /1.4/standards — data standards of the portal (DEC-019)."""

    def on_get(self, req, resp, **kwargs):
        from mcod.aed.models import DataStandard

        data = []
        for standard in DataStandard.objects.filter(is_active=True).order_by("name"):
            spec = standard.spec()
            attrs = standard.as_api_dict()
            attrs.update({
                "description": standard.description, "fields_count": len(spec.fields),
                "required_fields": spec.required, "merge": spec.merge, "max_invalid_ratio": standard.max_invalid_ratio,
                "datasets_count": standard.dataset_links.count(),
                "target_dataset_id": standard.target_dataset_id, "links": _standard_links(req, standard.code),
            })
            data.append(jsonapi.resource_object("data_standard", standard.code, attrs,
                                                self_link=_standard_links(req, standard.code)["schema"]))
        jsonapi.send(resp, req, data, count=len(data))


class StandardSchemaView:
    """GET /1.4/standards/{code}/schema — the structure of one standard."""

    def on_get(self, req, resp, code=None, **kwargs):
        standard = _standard_or_404(req, resp, code)
        if standard is None:
            return
        attrs = standard.spec().document()
        attrs["downloads"] = _standard_links(req, code)
        data = jsonapi.resource_object("data_standard_schema", code, attrs, self_link=attrs["downloads"]["schema"])
        jsonapi.send(resp, req, data)


class StandardSchemaFileView:
    """GET /1.4/standards/{code}/schema.{xlsx,csv,json} and table-schema.json."""

    def __init__(self, kind):
        self.kind = kind

    def on_get(self, req, resp, code=None, **kwargs):
        import json

        standard = _standard_or_404(req, resp, code)
        if standard is None:
            return
        spec = standard.spec()
        name = "{}-{}".format(code, spec.version)
        if self.kind == "xlsx":
            body, ctype, filename = spec.xlsx_bytes(), schema_export.XLSX_CONTENT_TYPE, name + ".xlsx"
        elif self.kind == "csv":
            body, ctype, filename = spec.csv_template().encode("utf-8-sig"), "text/csv; charset=utf-8", name + "-szablon.csv"
        elif self.kind == "json":
            body = json.dumps(spec.json_schema(), ensure_ascii=False, indent=2).encode("utf-8")
            ctype, filename = "application/schema+json", name + ".schema.json"
        else:
            body = json.dumps(spec.table_schema(), ensure_ascii=False, indent=2).encode("utf-8")
            ctype, filename = "application/json", name + ".table-schema.json"
        resp.status = falcon.HTTP_200
        resp.content_type = ctype
        resp.data = body
        resp.set_header("Content-Disposition", 'attachment; filename="{}"'.format(filename))


ROUTES += [
    ("/standards", StandardsListView()),
    ("/standards/{code}/schema", StandardSchemaView()),
    ("/standards/{code}/schema.xlsx", StandardSchemaFileView("xlsx")),
    ("/standards/{code}/schema.csv", StandardSchemaFileView("csv")),
    ("/standards/{code}/schema.json", StandardSchemaFileView("json")),
    ("/standards/{code}/table-schema.json", StandardSchemaFileView("table")),
    ("/standards/{code}/validate", AedValidateView()),
]

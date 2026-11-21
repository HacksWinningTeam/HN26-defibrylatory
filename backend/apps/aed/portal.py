"""dane.gov.pl-compatible API (``/api/1.4/...``), exports and the map GeoJSON (T04).

The envelope mirrors https://api.dane.gov.pl/1.4 (JSON:API: ``jsonapi``, ``links``, ``data``
with ``id/type/attributes/relationships/links``, ``meta`` with ``server_time``, ``path``,
``language``, ``relative_uri``, ``params``, ``count``); tabular rows use
``attributes.colN = {"repr", "val"}`` with ``meta.headers_map`` and ``meta.data_schema``.
"""

from __future__ import annotations

import json
import math
import uuid
from datetime import UTC, datetime
from urllib.parse import urlencode

from django.db.models import Q
from django.http import Http404, HttpResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.renderers import JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.aed import exports
from apps.aed.models import AED
from apps.aed.schema import FIELDS, SCHEMA_VERSION

PORTAL_TAG = "dane.gov.pl compatible (1.4)"
EXPORT_TAG = "Exports"
DATASET_ID = "1"
INSTITUTION_ID = "misja-aed"
ROW_NAMESPACE = uuid.UUID("6f1c2b1e-6a4e-4c51-9a3e-aed000000001")
MAX_PER_PAGE = 100

# id -> (format, title suffix, export path, openness score, visualization types, tabular)
RESOURCES = {
    "1": ("csv", "CSV", "/api/exports/aed.csv", 3, ["table", "map"], True),
    "2": ("xlsx", "XLSX", "/api/exports/aed.xlsx", 2, ["table"], True),
    "3": ("geojson", "GeoJSON", "/api/exports/aed.geojson", 3, ["map"], True),
    "4": ("json", "JSON", "/api/exports/aed.json", 3, ["table"], True),
    "5": ("xlsx", "Wzorcowy zakres danych (schemat)", "/api/schema-standard/aed-schema.xlsx",
          2, [], False),
}

PAGE_PARAMS = [
    OpenApiParameter("page", int, description="Page number (from 1)"),
    OpenApiParameter("per_page", int, description=f"Items per page (max {MAX_PER_PAGE})"),
]
ENVELOPE = OpenApiResponse(OpenApiTypes.OBJECT, description="JSON:API envelope as dane.gov.pl")


# --- envelope helpers ----------------------------------------------------------------------


OBJECT_KEY_ORDER = ("relationships", "attributes", "type", "links", "meta", "id")


def _ordered(obj: dict) -> dict:
    """Same key order as api.dane.gov.pl objects (cosmetic, visible in browsers)."""
    return {k: obj[k] for k in OBJECT_KEY_ORDER if k in obj}


def _abs(request: Request, path: str) -> str:
    return request.build_absolute_uri(path)


def _ts(value: datetime | None) -> str | None:
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ") if value else None


def _envelope(request: Request, data, *, links: dict | None = None, **meta) -> dict:
    params = {k: v for k, v in request.query_params.items()}
    return {
        "jsonapi": {"version": "1.4"},
        "links": links or {"self": request.build_absolute_uri()},
        "data": data,
        "meta": {
            **meta,
            "server_time": _ts(datetime.now(UTC)),
            "path": request.path.removeprefix("/api"),
            "language": "pl",
            "relative_uri": request.get_full_path().removeprefix("/api"),
            "params": params,
        },
    }


def _page(request: Request) -> tuple[int, int]:
    try:
        page = max(1, int(request.query_params.get("page", 1)))
        per_page = int(request.query_params.get("per_page", 20))
    except ValueError:
        page, per_page = 1, 20
    return page, min(max(1, per_page), MAX_PER_PAGE)


def _page_links(request: Request, page: int, per_page: int, count: int) -> dict:
    last = max(1, math.ceil(count / per_page))
    base = request.build_absolute_uri(request.path)
    other = {k: v for k, v in request.query_params.items() if k not in ("page", "per_page")}

    def url(p: int) -> str:
        return f"{base}?{urlencode({**other, 'per_page': per_page, 'page': p})}"

    links = {"last": url(last), "self": url(page)}  # same keys as api.dane.gov.pl
    if page > 1:
        links["prev"] = url(page - 1)
    if page < last:
        links["next"] = url(page + 1)
    return links


# --- object builders -----------------------------------------------------------------------


def _institution(request: Request) -> dict:
    return {
        "links": {"related": _abs(request, f"/api/1.4/institutions/{INSTITUTION_ID}")},
        "data": {"type": "institution", "id": INSTITUTION_ID},
    }


def dataset_object(request: Request) -> dict:
    modified = exports.last_modified()
    return _ordered({
        "id": DATASET_ID,
        "type": "dataset",
        "links": {"self": _abs(request, f"/api/1.4/datasets/{DATASET_ID}")},
        "attributes": {
            "title": exports.DATASET_TITLE,
            "notes": exports.DATASET_NOTES,
            "slug": exports.DATASET_SLUG,
            "categories": [{"id": "147", "code": "HEAL", "title": "Zdrowie"}],
            "category": None,
            "formats": ["csv", "xlsx", "geojson", "json"],
            "types": ["file"],
            "openness_scores": sorted({r[3] for r in RESOURCES.values()}),
            "license_chosen": None,
            "license_name": exports.LICENSE_NAME,
            "license_description": exports.LICENSE_NOTE,
            "update_frequency": exports.UPDATE_FREQUENCY,
            "keywords": exports.KEYWORDS,
            "regions": [{"name": "Polska", "region_id": "85633723",
                         "hierarchy_label": "Polska", "is_additional": False}],
            "source": None,
            "url": "",
            "created": _ts(modified),
            "modified": _ts(modified),
            "verified": _ts(modified),
            "views_count": 0,
            "downloads_count": 0,
            "has_dynamic_data": False,
            "has_high_value_data": True,
            "has_research_data": False,
            "has_high_value_data_from_ec_list": False,
            "visualization_types": ["table", "map"],
            "supplements": [],
            "likes_count": 0,
            "is_liked_by_current_user": False,
            "is_promoted": False,
            "image_url": "",
            "image_alt": "",
            "archived_resources_files_url": None,
            "license_condition_personal_data": None,
            "license_condition_default_cc40": False,
            "license_condition_custom_description": "",
            "license_condition_timestamp": None,
            "license_condition_db_or_copyrighted": exports.LICENSE_NOTE,
            "license_condition_original": None,
            "current_condition_descriptions": {},
            "schema_version": SCHEMA_VERSION,
        },
        "relationships": {
            "resources": {
                "meta": {"count": len(RESOURCES)},
                "links": {"related": _abs(request, f"/api/1.4/datasets/{DATASET_ID}/resources")},
            },
            "showcases": {"meta": {"count": 0}, "links": {"related": None}},
            "institution": _institution(request),
        },
    })


def resource_object(request: Request, rid: str) -> dict:
    fmt, suffix, path, score, vis, tabular = RESOURCES[rid]
    url = _abs(request, path)
    modified = exports.last_modified()
    relationships = {
        "dataset": {
            "links": {"related": _abs(request, f"/api/1.4/datasets/{DATASET_ID}")},
            "data": {"type": "dataset", "id": DATASET_ID},
        },
        "institution": _institution(request),
        "chart": {"links": {"related": None}, "data": None},
    }
    if tabular:
        relationships["tabular_data"] = {
            "links": {"related": _abs(request, f"/api/1.4/resources/{rid}/data")},
            "data": {"type": "tabular_data", "id": rid},
        }
    return _ordered({
        "id": rid,
        "type": "resource",
        "links": {"self": _abs(request, f"/api/1.4/resources/{rid}")},
        "attributes": {
            "title": f"{exports.DATASET_TITLE} ({suffix})" if tabular else suffix,
            "description": exports.DATASET_NOTES if tabular else
            "Wzorcowy zakres danych o defibrylatorach AED (arkusz xlsx).",
            "format": fmt,
            "media_type": "file",
            "openness_score": score,
            "file_url": url,
            "download_url": url,
            "link": url,
            "file_size": None,
            "csv_file_url": _abs(request, RESOURCES["1"][2]) if tabular else None,
            "csv_download_url": _abs(request, RESOURCES["1"][2]) if tabular else None,
            "jsonld_file_url": None,
            "files": [{"download_url": url, "format": fmt, "file_size": None,
                       "openness_score": score, "compressed_file_format": None}],
            "visualization_types": vis,
            "category": None,
            "data_date": modified.date().isoformat() if modified else None,
            "language": "pl",
            "regions": [{"name": "Polska", "region_id": "85633723",
                         "hierarchy_label": "Polska", "is_additional": False}],
            "created": _ts(modified),
            "modified": _ts(modified),
            "verified": _ts(modified),
            "views_count": 0,
            "downloads_count": 0,
            "has_dynamic_data": False,
            "has_high_value_data": True,
            "contains_protected_data": False,
            "special_signs": [],
            "supplements": [],
            "csv_file_size": None,
            "jsonld_download_url": None,
            "jsonld_file_size": None,
            "is_chart_creation_blocked": True,
            "has_high_value_data_from_ec_list": False,
            "has_research_data": False,
        },
        "relationships": relationships,
    })


def _row_uuid(id_aed: str) -> str:
    return str(uuid.uuid5(ROW_NAMESPACE, id_aed))


def _cell(value) -> dict:
    if value is None:
        return {"repr": "", "val": None}
    if isinstance(value, bool):
        return {"repr": "true" if value else "false", "val": value}
    return {"repr": str(value), "val": value}


def row_object(request: Request, rid: str, data: dict, row_no: int, updated) -> dict:
    row_id = _row_uuid(data["id_aed"])
    return _ordered({
        "id": row_id,
        "type": "row",
        "links": {"self": _abs(request, f"/api/1.4/resources/{rid}/data/{row_id}")},
        "attributes": {f"col{i}": _cell(data.get(f.name)) for i, f in enumerate(FIELDS, start=1)},
        "relationships": {"resource": {
            "links": {"related": _abs(request, f"/api/1.4/resources/{rid}")},
            "data": {"type": "resource", "id": rid},
        }},
        "meta": {"updated_at": _ts(updated), "row_no": row_no},
    })


def table_meta() -> dict:
    return {
        "headers_map": {f"col{i}": f.name for i, f in enumerate(FIELDS, start=1)},
        "data_schema": {
            "fields": [
                {"name": f"col{i}", "type": f.type, "format": "default"}
                for i, f in enumerate(FIELDS, start=1)
            ],
            "missingValues": [],
        },
        "aggregations": {},
    }


def _search(qs, q: str):
    if not q:
        return qs
    cond = Q()
    for key in ("nazwa", "miejscowosc", "nazwa_ulicy", "opis_lokalizacji", "dysponent"):
        cond |= Q(**{f"data__{key}__icontains": q})
    return qs.filter(cond)


# --- views ---------------------------------------------------------------------------------


class _Public(APIView):
    """Public, JSON-only (like api.dane.gov.pl — no browsable HTML even in DEBUG)."""

    authentication_classes = []
    permission_classes = []
    renderer_classes = [JSONRenderer]


class DatasetListView(_Public):
    @extend_schema(tags=[PORTAL_TAG], summary="Datasets (dane.gov.pl /1.4/datasets)",
                   operation_id="dgp_datasets_list",
                   parameters=[*PAGE_PARAMS, OpenApiParameter("q", str)],
                   responses={200: ENVELOPE})
    def get(self, request: Request) -> Response:
        q = request.query_params.get("q", "").lower()
        items = [dataset_object(request)]
        if q and q not in (exports.DATASET_TITLE + " " + " ".join(exports.KEYWORDS)).lower():
            items = []
        page, per_page = _page(request)
        return Response(_envelope(request, items[(page - 1) * per_page: page * per_page],
                                  links=_page_links(request, page, per_page, len(items)),
                                  count=len(items), aggregations={}))


class DatasetDetailView(_Public):
    @extend_schema(tags=[PORTAL_TAG], summary="Dataset detail (dane.gov.pl /1.4/datasets/{id})",
                   operation_id="dgp_dataset_detail",
                   responses={200: ENVELOPE, 404: OpenApiResponse(description="Not found")})
    def get(self, request: Request, dataset_id: str) -> Response:
        if dataset_id.split(",")[0] != DATASET_ID:
            raise Http404
        return Response(_envelope(request, dataset_object(request)))


class DatasetResourcesView(_Public):
    @extend_schema(tags=[PORTAL_TAG], summary="Resources of a dataset",
                   operation_id="dgp_dataset_resources",
                   parameters=PAGE_PARAMS, responses={200: ENVELOPE, 404: OpenApiResponse()})
    def get(self, request: Request, dataset_id: str) -> Response:
        if dataset_id.split(",")[0] != DATASET_ID:
            raise Http404
        items = [resource_object(request, rid) for rid in RESOURCES]
        page, per_page = _page(request)
        return Response(_envelope(request, items[(page - 1) * per_page: page * per_page],
                                  links=_page_links(request, page, per_page, len(items)),
                                  count=len(items), aggregations={}))


class ResourceDetailView(_Public):
    @extend_schema(tags=[PORTAL_TAG], summary="Resource detail (dane.gov.pl /1.4/resources/{id})",
                   operation_id="dgp_resource_detail",
                   responses={200: ENVELOPE, 404: OpenApiResponse()})
    def get(self, request: Request, resource_id: str) -> Response:
        rid = resource_id.split(",")[0]
        if rid not in RESOURCES:
            raise Http404
        return Response(_envelope(request, resource_object(request, rid)))


class ResourceDataView(_Public):
    @extend_schema(
        tags=[PORTAL_TAG],
        summary="Tabular data rows (dane.gov.pl /1.4/resources/{id}/data)",
        operation_id="dgp_resource_data",
        parameters=[*PAGE_PARAMS, OpenApiParameter("q", str, description="Full-text filter")],
        responses={200: ENVELOPE, 404: OpenApiResponse()},
    )
    def get(self, request: Request, resource_id: str) -> Response:
        rid = resource_id.split(",")[0]
        if rid not in RESOURCES or not RESOURCES[rid][5]:
            raise Http404
        qs = _search(AED.objects.order_by("id_aed"), request.query_params.get("q", "").strip())
        count = qs.count()
        page, per_page = _page(request)
        start = (page - 1) * per_page
        data = [
            row_object(request, rid, d, start + i + 1, updated)
            for i, (d, updated) in enumerate(
                qs.values_list("data", "updated_at")[start: start + per_page]
            )
        ]
        return Response(_envelope(request, data,
                                  links=_page_links(request, page, per_page, count),
                                  count=count, **table_meta()))


class ResourceRowView(_Public):
    @extend_schema(tags=[PORTAL_TAG], summary="Single tabular row", operation_id="dgp_resource_row",
                   responses={200: ENVELOPE, 404: OpenApiResponse()})
    def get(self, request: Request, resource_id: str, row_id: str) -> Response:
        rid = resource_id.split(",")[0]
        if rid not in RESOURCES or not RESOURCES[rid][5]:
            raise Http404
        for i, (data, updated) in enumerate(
            AED.objects.order_by("id_aed").values_list("data", "updated_at"), start=1
        ):
            if _row_uuid(data["id_aed"]) == row_id:
                return Response(_envelope(request, row_object(request, rid, data, i, updated),
                                          **table_meta()))
        raise Http404


class ExportView(_Public):
    @extend_schema(
        tags=[EXPORT_TAG],
        summary="Download the national AED dataset (csv | json | geojson | xlsx)",
        responses={200: OpenApiResponse(OpenApiTypes.BINARY), 404: OpenApiResponse()},
    )
    def get(self, request: Request, fmt: str) -> HttpResponse:
        if fmt not in exports.EXPORTS:
            raise Http404
        content, content_type = exports.export(fmt)
        response = HttpResponse(content, content_type=content_type)
        response["Content-Disposition"] = f'attachment; filename="aed.{fmt}"'
        return response


class AedMapView(_Public):
    @extend_schema(
        tags=["Map"],
        summary="Lightweight GeoJSON of all merged AEDs for the map (contract DEC-008)",
        parameters=[
            OpenApiParameter("q", str, description="Filter by name/city/street/description"),
            OpenApiParameter("bbox", str, description="minLon,minLat,maxLon,maxLat"),
        ],
        responses={200: OpenApiResponse(OpenApiTypes.OBJECT, description="GeoJSON"),
                   400: OpenApiResponse(description="Invalid bbox")},
    )
    def get(self, request: Request) -> HttpResponse:
        q = request.query_params.get("q", "").strip()
        bbox = request.query_params.get("bbox", "").strip()
        if not q and not bbox:
            return HttpResponse(exports.map_geojson_all(),
                                content_type=exports.GEOJSON_CONTENT_TYPE)
        qs = _search(AED.objects.order_by("id_aed"), q)
        if bbox:
            try:
                min_lon, min_lat, max_lon, max_lat = (float(v) for v in bbox.split(","))
            except ValueError:
                return HttpResponse(
                    json.dumps({"detail": "bbox must be minLon,minLat,maxLon,maxLat"}),
                    status=400, content_type="application/json",
                )
            qs = qs.filter(lon__gte=min_lon, lon__lte=max_lon, lat__gte=min_lat, lat__lte=max_lat)
        features = exports.map_features(qs)
        payload = {"type": "FeatureCollection",
                   "meta": {"count": len(features), "generated_at": _ts(datetime.now(UTC)),
                            "license": exports.LICENSE_NAME},
                   "features": features}
        return HttpResponse(json.dumps(payload, ensure_ascii=False),
                            content_type=exports.GEOJSON_CONTENT_TYPE)


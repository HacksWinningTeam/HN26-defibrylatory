"""API views for the standard AED schema and its downloadable artefacts."""

import json

from django.http import HttpResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.aed import schema_export
from apps.aed.serializers import SchemaDocumentSerializer, SourcesReportSerializer
from apps.aed.sources_report import build_report

SCHEMA_TAG = "Standard AED schema"


def _download(content: str | bytes, content_type: str, filename: str) -> HttpResponse:
    response = HttpResponse(content, content_type=content_type)
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def _json_download(payload: dict, filename: str) -> HttpResponse:
    body = json.dumps(payload, ensure_ascii=False, indent=2)
    return _download(body, "application/schema+json; charset=utf-8", filename)


class SchemaDocumentView(APIView):
    """Standard AED schema as JSON."""

    authentication_classes = []
    permission_classes = []

    @extend_schema(
        tags=[SCHEMA_TAG],
        summary="Standard AED schema (field list)",
        responses={200: SchemaDocumentSerializer},
    )
    def get(self, request: Request) -> Response:
        return Response(SchemaDocumentSerializer(schema_export.schema_document()).data)


class _FileView(APIView):
    authentication_classes = []
    permission_classes = []


class SchemaXlsxView(_FileView):
    @extend_schema(
        tags=[SCHEMA_TAG],
        summary="Download the schema as an Excel workbook (.xlsx)",
        responses={200: OpenApiResponse(OpenApiTypes.BINARY, description="xlsx file")},
    )
    def get(self, request: Request) -> HttpResponse:
        return _download(
            schema_export.xlsx_bytes(), schema_export.XLSX_CONTENT_TYPE, "aed-schema.xlsx"
        )


class SchemaCsvTemplateView(_FileView):
    @extend_schema(
        tags=[SCHEMA_TAG],
        summary="Download a CSV template (header + example rows)",
        responses={200: OpenApiResponse(OpenApiTypes.STR, description="CSV file")},
    )
    def get(self, request: Request) -> HttpResponse:
        # UTF-8 BOM so that Excel opens Polish characters correctly.
        body = "﻿" + schema_export.csv_template()
        return _download(body, "text/csv; charset=utf-8", "aed-template.csv")


class SchemaJsonSchemaView(_FileView):
    @extend_schema(
        tags=[SCHEMA_TAG],
        summary="Download the JSON Schema (draft 2020-12) of one AED record",
        responses={200: OpenApiResponse(OpenApiTypes.OBJECT, description="JSON Schema")},
    )
    def get(self, request: Request) -> HttpResponse:
        return _json_download(schema_export.json_schema(), "aed-schema.json")


class SchemaTableSchemaView(_FileView):
    @extend_schema(
        tags=[SCHEMA_TAG],
        summary="Download the Frictionless Table Schema for the CSV form",
        responses={200: OpenApiResponse(OpenApiTypes.OBJECT, description="Table Schema")},
    )
    def get(self, request: Request) -> HttpResponse:
        return _json_download(schema_export.table_schema(), "table-schema.json")


class SourcesReportView(APIView):
    """Harvested sources with record counts, quality flags and coverage of the standard schema."""

    authentication_classes = []
    permission_classes = []

    @extend_schema(
        tags=["Sources"],
        summary="Harvested AED sources and their reference scope (schema coverage)",
        responses={200: SourcesReportSerializer},
    )
    def get(self, request: Request) -> Response:
        return Response(SourcesReportSerializer(build_report()).data)

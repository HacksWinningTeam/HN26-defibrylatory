"""URL routing for the AED API."""

from django.urls import path

from apps.aed import views

urlpatterns = [
    path("sources/", views.SourcesReportView.as_view(), name="aed-sources"),
    path("schema-standard/", views.SchemaDocumentView.as_view(), name="aed-schema"),
    path(
        "schema-standard/aed-schema.xlsx",
        views.SchemaXlsxView.as_view(),
        name="aed-schema-xlsx",
    ),
    path(
        "schema-standard/aed-template.csv",
        views.SchemaCsvTemplateView.as_view(),
        name="aed-schema-csv",
    ),
    path(
        "schema-standard/aed-schema.json",
        views.SchemaJsonSchemaView.as_view(),
        name="aed-schema-json",
    ),
    path(
        "schema-standard/table-schema.json",
        views.SchemaTableSchemaView.as_view(),
        name="aed-table-schema",
    ),
]

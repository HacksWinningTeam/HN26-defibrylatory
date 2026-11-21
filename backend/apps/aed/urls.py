"""URL routing for the AED API."""

from django.urls import path

from apps.aed import portal, views

urlpatterns = [
    path("1.4/datasets", portal.DatasetListView.as_view(), name="dgp-datasets"),
    path("1.4/datasets/<str:dataset_id>", portal.DatasetDetailView.as_view(), name="dgp-dataset"),
    path(
        "1.4/datasets/<str:dataset_id>/resources",
        portal.DatasetResourcesView.as_view(),
        name="dgp-dataset-resources",
    ),
    path(
        "1.4/resources/<str:resource_id>", portal.ResourceDetailView.as_view(), name="dgp-resource"
    ),
    path(
        "1.4/resources/<str:resource_id>/data",
        portal.ResourceDataView.as_view(),
        name="dgp-resource-data",
    ),
    path(
        "1.4/resources/<str:resource_id>/data/<str:row_id>",
        portal.ResourceRowView.as_view(),
        name="dgp-resource-row",
    ),
    path("exports/aed.<str:fmt>", portal.ExportView.as_view(), name="aed-export"),
    path("aed/", portal.AedMapView.as_view(), name="aed-map"),
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

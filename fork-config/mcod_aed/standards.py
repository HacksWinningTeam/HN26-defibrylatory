"""The `aed-pl` data standard record (seeded by migration, refreshed by `ensure_aed_standard`)."""
from mcod.aed import schema
from mcod.aed.schema_export import json_schema

AED_STANDARD_CODE = schema.SCHEMA_NAME  # "aed-pl"


def aed_standard_defaults():
    return {
        "name": "Dane AED – wzorcowy zakres danych",
        "version": schema.SCHEMA_VERSION,
        "description": schema.SCHEMA_DESCRIPTION,
        "json_schema": json_schema(),
    }


def ensure_aed_standard(DataStandard=None):
    """Create or refresh the `aed-pl` standard (keeps `target_dataset` and `max_invalid_ratio`)."""
    if DataStandard is None:
        from mcod.aed.models import DataStandard
    standard, _ = DataStandard.objects.update_or_create(
        code=AED_STANDARD_CODE, defaults=aed_standard_defaults()
    )
    return standard


def get_dataset_standard(dataset_id):
    """DataStandard of a dataset or None (one query)."""
    from mcod.aed.models import DatasetStandard

    link = DatasetStandard.objects.select_related("standard").filter(dataset_id=dataset_id).first()
    return link.standard if link else None

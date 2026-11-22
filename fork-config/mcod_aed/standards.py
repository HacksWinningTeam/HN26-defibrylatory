"""The `aed-pl` data standard record (seeded by migration, refreshed by `ensure_aed_standard`)."""
import os

from mcod.aed import schema
from mcod.aed.schema_export import json_schema

AED_STANDARD_CODE = schema.SCHEMA_NAME  # "aed-pl"


def aed_standard_defaults():
    from mcod.aed.spec import aed_definition

    definition = aed_definition()
    return {
        "name": "Dane AED – wzorcowy zakres danych",
        "version": schema.SCHEMA_VERSION,
        "description": schema.SCHEMA_DESCRIPTION,
        "json_schema": json_schema(),
        # DEC-019: mirrored into the data format (display + generic API); the AED engine still uses schema.py
        "fields": definition["fields"],
        "merge": definition["merge"],
        "discovery": definition["discovery"],
        "publish": definition["publish"],
    }


def ensure_aed_standard(DataStandard=None):
    """Create or refresh the `aed-pl` standard (keeps `target_dataset` and `max_invalid_ratio`)."""
    if DataStandard is None:
        from mcod.aed.models import DataStandard
    # Migration 0002 passes the historical model (before 0006 added fields/merge/...): only set what exists.
    existing = {f.name for f in DataStandard._meta.get_fields()}
    defaults = {k: v for k, v in aed_standard_defaults().items() if k in existing}
    standard, _ = DataStandard.objects.update_or_create(code=AED_STANDARD_CODE, defaults=defaults)
    return standard


def get_dataset_standard(dataset_id):
    """DataStandard of a dataset or None (one query)."""
    from mcod.aed.models import DatasetStandard

    link = DatasetStandard.objects.select_related("standard").filter(dataset_id=dataset_id).first()
    return link.standard if link else None


STANDARDS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "standards")


def load_standard(data, DataStandard=None):
    """Create or update a data-defined standard from its JSON definition (DEC-019). -> (standard, created)."""
    from mcod.aed.spec import StandardSpec

    if DataStandard is None:
        from mcod.aed.models import DataStandard
    spec = StandardSpec.from_dict(data)
    if spec.code == AED_STANDARD_CODE:
        raise ValueError("Standard aed-pl jest zdefiniowany w kodzie (schema.py) – użyj ensure_aed_standard().")
    return DataStandard.objects.update_or_create(code=spec.code, defaults={
        "name": spec.name, "version": spec.version, "description": spec.description,
        "fields": spec.fields, "merge": spec.merge, "discovery": spec.discovery, "publish": spec.publish,
        "json_schema": spec.json_schema(),
    })

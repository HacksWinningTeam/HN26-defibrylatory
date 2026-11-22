"""All hooks of `mcod.aed` into upstream dane.gov.pl code, applied from `AedConfig.ready()`.

No upstream file is edited (DEC-014/015):
  * api:   our Falcon routes are appended to `mcod.routes.routes` (read by `get_api_app()` after
           `django.setup()`), and `data_standard` is added to the dataset API attributes.
  * admin: "Standard danych" field in the dataset admin form (saved as `DatasetStandard`).
Every hook is idempotent and guarded so a failure never takes the portal down.
"""
import logging

from django.conf import settings

logger = logging.getLogger("mcod")

_installed = set()


def _component():
    return str(getattr(settings, "COMPONENT", "admin")).lower()


def install():
    component = _component()
    if component == "api":
        _safe(register_routes)
        _safe(patch_dataset_api)
    if component == "admin":
        _safe(patch_dataset_admin)


def _safe(hook):
    try:
        hook()
    except Exception:  # pragma: no cover - never break the portal because of the plugin
        logger.exception("mcod.aed: hook %s failed", hook.__name__)


# --- API -------------------------------------------------------------------------------------


def register_routes():
    """Append `mcod.aed.views.ROUTES` to the upstream route list (served under /1.4/...)."""
    if "routes" in _installed:
        return
    from mcod import routes as upstream
    from mcod.aed.views import ROUTES

    # mcod/routes.py duplicates every route with a "/{api_version}" prefix at import time
    # (`/1.4/...`, used by the portal and docs), so we add both forms like upstream routes have.
    existing = {route[0] for route in upstream.routes}
    for path, view in ROUTES:
        for prefixed in (path, "/{api_version}" + path):
            if prefixed not in existing:
                upstream.routes.append((prefixed, view))
    _installed.add("routes")


def data_standard_for(obj):
    """`{code, name, version}` of the standard a dataset (model or ES hit) belongs to, else None."""
    from mcod.aed.standards import get_dataset_standard

    dataset_id = getattr(obj, "id", None)
    if dataset_id is None and isinstance(obj, dict):
        dataset_id = obj.get("id")
    if dataset_id is None:
        return None
    standard = get_dataset_standard(int(dataset_id))
    return standard.as_api_dict() if standard else None


def patch_dataset_api():
    """Add `data_standard` to `attributes` of /1.4/datasets and /1.4/datasets/{id}."""
    if "dataset_api" in _installed:
        return
    from marshmallow import fields

    from mcod.datasets.serializers import DatasetApiAttrs

    DatasetApiAttrs._declared_fields["data_standard"] = fields.Function(
        serialize=data_standard_for, dump_only=True
    )
    _installed.add("dataset_api")


# --- Admin -----------------------------------------------------------------------------------

STANDARD_FIELD = "data_standard"


def patch_dataset_admin():
    """Dataset admin: "Standard danych" select on the General tab, persisted as DatasetStandard."""
    if "dataset_admin" in _installed:
        return
    from django import forms

    from mcod.aed.models import DataStandard, DatasetStandard
    from mcod.datasets import admin as dataset_admin

    mixin = dataset_admin.DatasetAdminMixin
    base_form = mixin.form

    class DatasetFormWithStandard(base_form):
        data_standard = forms.ModelChoiceField(
            queryset=DataStandard.objects.filter(is_active=True),
            required=False,
            label="Standard danych",
            empty_label="— brak (zbiór samodzielny) —",
            help_text=(
                "Zbiór jest częścią większego zbioru zbiorczego, np. „Dane AED”. Dane jego zasobów "
                "są automatycznie sprawdzane ze strukturą standardu i agregowane."
            ),
        )

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if self.instance is not None and self.instance.pk and STANDARD_FIELD in self.fields:
                link = DatasetStandard.objects.filter(dataset_id=self.instance.pk).first()
                if link:
                    self.initial[STANDARD_FIELD] = link.standard_id

    DatasetFormWithStandard.__name__ = base_form.__name__
    mixin.form = DatasetFormWithStandard

    original_get_fieldsets = mixin.get_fieldsets

    def get_fieldsets(self, request, obj=None):
        fieldsets = original_get_fieldsets(self, request, obj)
        result = []
        added = False
        for name, options in fieldsets:
            options = dict(options)
            fields_list = list(options.get("fields", ()))
            if not added and "suit-tab-general" in options.get("classes", ()):
                anchor = next(
                    (f for f in ("categories", "categories_list", "organization") if f in fields_list),
                    None,
                )
                index = fields_list.index(anchor) + 1 if anchor else len(fields_list)
                if STANDARD_FIELD not in fields_list:
                    fields_list.insert(index, STANDARD_FIELD)
                added = True
            options["fields"] = fields_list
            result.append((name, options))
        return result

    mixin.get_fieldsets = get_fieldsets

    original_save_model = mixin.save_model

    def save_model(self, request, obj, form, change):
        original_save_model(self, request, obj, form, change)
        if STANDARD_FIELD in getattr(form, "cleaned_data", {}):
            save_dataset_standard(obj, form.cleaned_data.get(STANDARD_FIELD))

    mixin.save_model = save_model
    _installed.add("dataset_admin")


def save_dataset_standard(dataset, standard):
    """Set (or clear with None) the 'Standard danych' of a dataset."""
    from mcod.aed.models import DatasetStandard

    if standard is None:
        DatasetStandard.objects.filter(dataset_id=dataset.pk).delete()
        return None
    link, _ = DatasetStandard.objects.update_or_create(
        dataset_id=dataset.pk, defaults={"standard": standard}
    )
    return link

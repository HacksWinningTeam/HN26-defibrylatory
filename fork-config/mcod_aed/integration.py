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
        _safe(patch_resource_form)
        _safe(patch_resource_admin_messages)
    if component == "celery":
        _safe(connect_celery_hooks)


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


def save_dataset_standard(dataset, standard, revalidate=True):
    """Set (or clear with None) the 'Standard danych' of a dataset; re-validate its resources on change."""
    from mcod.aed.models import DatasetStandard

    current = DatasetStandard.objects.filter(dataset_id=dataset.pk).first()
    if standard is None:
        if current:
            current.delete()
        return None
    link, _ = DatasetStandard.objects.update_or_create(
        dataset_id=dataset.pk, defaults={"standard": standard}
    )
    if revalidate and (current is None or current.standard_id != standard.pk):
        from mcod.aed.resource_validation import queue_dataset_validation

        queue_dataset_validation(dataset.pk)
    return link


# --- Automatic validation hooks (T14, DEC-015) ----------------------------------------------------


def connect_celery_hooks():
    """celery: after the portal's resource/file validation tasks, validate against the standard."""
    if "celery" in _installed:
        return
    from mcod.aed.tasks import connect_upstream_hooks

    connect_upstream_hooks()
    _installed.add("celery")


def patch_resource_form():
    """admin: refuse to publish a resource whose data fails its dataset's standard (blocking)."""
    if "resource_form" in _installed:
        return
    from django import forms

    from mcod.resources import forms as resource_forms

    form_class = resource_forms.ResourceForm
    original_clean = form_class.clean

    def clean(self):
        data = original_clean(self)
        try:
            messages = standard_errors_for_form(self, data)
        except Exception:  # never break the admin because of the plugin
            logger.exception("mcod.aed: resource form validation failed")
            messages = []
        if messages:
            # attached to the file field so the admin shows it next to the upload (not as "__all__")
            self.add_error("file" if "file" in self.fields else None, forms.ValidationError(messages))
        return data

    form_class.clean = clean
    _installed.add("resource_form")


def standard_errors_for_form(form, data):
    """Messages that block saving a published resource of a dataset with a standard ([] = OK)."""
    from mcod.aed import resource_validation, validation
    from mcod.aed.models import ResourceStandardValidation
    from mcod.aed.standards import get_dataset_standard

    if data is None or data.get("status", getattr(form.instance, "status", None)) != "published":
        return []
    dataset = data.get("dataset") or getattr(form.instance, "dataset", None)
    if dataset is None or not getattr(dataset, "pk", None):
        return []
    standard = get_dataset_standard(dataset.pk)
    if standard is None or not standard.is_active:
        return []
    upload = data.get("file")
    header = "Dane nie spełniają standardu „{}” – zasobu nie można opublikować. Popraw plik albo zapisz zasób jako szkic.".format(standard.name)
    if upload and hasattr(upload, "read"):
        position = upload.tell() if hasattr(upload, "tell") else 0
        raw = upload.read()
        upload.seek(position)
        try:
            report = validation.validate_for_standard(raw, standard=standard, filename=getattr(upload, "name", None))
        except validation.ValidationInputError as exc:
            return [header, str(exc)]
        if report["blocking"]:
            return [header] + resource_validation.summarize_for_form(report)
        return []
    # No new file: publishing a resource that is currently blocked is refused too.
    if form.instance is not None and form.instance.pk:
        stored = ResourceStandardValidation.objects.filter(resource_id=form.instance.pk, blocking=True).first()
        if stored:
            return [header] + list(stored.blocking_reasons) + [
                "wiersz {}: {}".format(e["row"], e["message"]) for e in stored.errors[:10]
            ]
    return []


def patch_resource_admin_messages():
    """admin: on a resource page of a standard dataset show the stored validation result."""
    if "resource_admin_messages" in _installed:
        return
    from django.contrib import admin, messages

    from mcod.resources.models import Resource

    model_admin = admin.site._registry.get(Resource)
    if model_admin is None:
        return
    admin_class = type(model_admin)
    original_change_view = admin_class.change_view

    def change_view(self, request, object_id, form_url="", extra_context=None):
        if request.method == "GET":
            try:
                add_validation_message(request, object_id)
            except Exception:  # pragma: no cover
                logger.exception("mcod.aed: validation message failed")
        return original_change_view(self, request, object_id, form_url, extra_context)

    admin_class.change_view = change_view
    _installed.add("resource_admin_messages")


def add_validation_message(request, object_id):
    from django.contrib import messages

    from mcod.aed.models import ResourceStandardValidation

    obj = ResourceStandardValidation.objects.select_related("standard").filter(resource_id=object_id).first()
    if obj is None:
        return
    link = "/1.4/resources/{}/standard-validation".format(object_id)
    text = "Standard „{}”: {} – wierszy {}, błędnych {}. Raport: API {}".format(
        obj.standard.name, obj.get_status_display(), obj.rows_total, obj.rows_invalid, link)
    if obj.blocking:
        reasons = " ".join(obj.blocking_reasons)
        errors = "; ".join("wiersz {}: {}".format(e["row"], e["message"]) for e in obj.errors[:3])
        messages.error(request, "ZASÓB ZABLOKOWANY (szkic). {} {} {}".format(text, reasons, errors))
    elif obj.status == obj.STATUS_VALID:
        messages.success(request, text)
    else:
        messages.warning(request, text)
    if not obj.blocking:
        note = auto_aggregation_note(obj.standard, object_id)
        if note:
            messages.info(request, note)


def auto_aggregation_note(standard, resource_id):
    """Text about the automatic refresh of the common dataset triggered by this resource (DEC-020)."""
    from mcod.aed.models import AedImportRun
    from mcod.datasets.models import Dataset

    title = Dataset.raw.filter(pk=standard.target_dataset_id).values_list("title", flat=True).first() \
        or (standard.publish or {}).get("title") or standard.name
    marker = "zasób {} ".format(resource_id)
    run = AedImportRun.objects.filter(standard=standard, triggered_by__contains=marker).order_by("-pk").first()
    if run is None:
        from django.core.cache import cache

        from mcod.aed.resource_validation import auto_aggregation_key

        try:
            queued = str(cache.get(auto_aggregation_key(standard))) == str(resource_id)
        except Exception:
            queued = False
        return "Zbiór zbiorczy „{}” zostanie odświeżony automatycznie (agregacja w kolejce).".format(
            title) if queued else ""
    if run.status == run.STATUS_RUNNING:
        return "Zbiór zbiorczy „{}” jest właśnie odświeżany automatycznie (agregacja #{}).".format(title, run.pk)
    if run.status == run.STATUS_OK:
        return ("Zbiór zbiorczy „{}” odświeżony automatycznie po przyjęciu tego zasobu: {} źródeł → {} obiektów "
                "(agregacja #{}).").format(title, run.sources_count, run.devices_count, run.pk)
    return "Automatyczna agregacja #{} zakończyła się błędem – szczegóły w „Agregacje”.".format(run.pk)

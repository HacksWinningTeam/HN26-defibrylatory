"""Idempotent creation of institutions / datasets / resources in the portal (T12, T13).

Pattern of upstream `mcod/resources/dga_utils.py` and T06: file resources are uploaded as the main
`ResourceFile` (the portal then validates + indexes them); connected APIs are API-type link resources.
"""
import hashlib
import io
import zipfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

LICENSE_BY_NAME = {"CC0 1.0": 1, "CC BY 4.0": 2, "CC BY-SA 4.0": 3}
FREQUENCY_BY_LABEL = {
    "codziennie": "daily", "daily": "daily", "co tydzień": "weekly", "weekly": "weekly",
    "co miesiąc": "monthly", "monthly": "monthly", "co kwartał": "quarterly", "quarterly": "quarterly",
    "co pół roku": "everyHalfYear", "co rok": "yearly", "yearly": "yearly",
    "nieregularnie": "irregular", "irregular": "irregular",
    "jednorazowe udostępnienie": "notPlanned", "nie dotyczy": "notPlanned",
}
MIMETYPES = {
    "csv": "text/csv", "json": "application/json", "geojson": "application/geo+json",
    "xml": "application/xml", "gml": "application/gml+xml",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
FLAG_DEFAULTS = dict(
    has_dynamic_data=False, has_high_value_data=False, has_high_value_data_from_ec_list=False,
    has_research_data=False,
)


def admin_user():
    from django.contrib.auth import get_user_model

    user = get_user_model().objects.filter(is_superuser=True).order_by("id").first()
    if user is None:
        raise RuntimeError("No superuser in the portal DB (run fork-config/setup.sh first)")
    return user


def frequency_code(label):
    if not label:
        return "irregular"
    return FREQUENCY_BY_LABEL.get(str(label).strip().lower(), "irregular")


def content_digest(data, filename=""):
    """sha256 ignoring XLSX creation timestamps (docProps/core.xml)."""
    if filename.endswith(".xlsx"):
        try:
            h = hashlib.sha256()
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                for name in sorted(zf.namelist()):
                    if name != "docProps/core.xml":
                        h.update(name.encode())
                        h.update(zf.read(name))
            return h.hexdigest()
        except zipfile.BadZipFile:
            pass
    return hashlib.sha256(data).hexdigest()


def ensure_organization(title, institution_type="local", **extra):
    from mcod.organizations.models import Organization

    user = admin_user()
    org = Organization.raw.filter(title=title, is_removed=False).first()
    fields = dict(institution_type=institution_type, status="published", modified_by=user)
    fields.update({k: v for k, v in extra.items() if v})
    if org is None:
        fields.setdefault("city", "—")
        fields.setdefault("postal_code", "00-000")
        fields.setdefault("street", "—")
        fields.setdefault("email", "kontakt@example.org")
        fields.setdefault("tel", "000000000")
        fields.setdefault("regon", "000000000")
        org = Organization.objects.create(title=title, created_by=user, **fields)
        return org, "created"
    changed = False
    for key, value in fields.items():
        if key != "modified_by" and getattr(org, key) != value:
            setattr(org, key, value)
            changed = True
    if changed:
        org.save()
    return org, "updated" if changed else "unchanged"


def ensure_dataset(org, title, ext_ident, notes, standard=None, tags=("AED", "defibrylatory", "zdrowie"),
                   license_name=None, license_text=None, update_frequency="irregular", url=None):
    """Dataset matched by ext_ident (or title); category HEAL; 'Standard danych' set (DEC-015)."""
    from mcod.aed.integration import save_dataset_standard
    from mcod.categories.models import Category
    from mcod.datasets.models import Dataset
    from mcod.tags.models import Tag

    user = admin_user()
    ds = Dataset.raw.filter(ext_ident=ext_ident, is_removed=False).first()
    if ds is None:
        ds = Dataset.raw.filter(title=title, organization=org, is_removed=False).first()
    fields = dict(
        title=title, notes=notes, organization=org, status="published", update_frequency=update_frequency,
        url=url, ext_ident=ext_ident, is_update_notification_enabled=False, modified_by=user, **FLAG_DEFAULTS
    )
    if license_name in LICENSE_BY_NAME:
        fields["license_chosen"] = LICENSE_BY_NAME[license_name]
        fields["license_condition_source"] = license_name != "CC0 1.0"
    if license_text:
        fields["license_condition_db_or_copyrighted"] = license_text
    if ds is None:
        ds = Dataset.objects.create(created_by=user, **fields)
        action = "created"
    else:
        for key, value in fields.items():
            setattr(ds, key, value)
        ds.save()
        action = "updated"
    heal = Category.objects.filter(code="HEAL").order_by("id").first()
    if heal is not None:
        ds.categories.set([heal])
    tag_objs = []
    for name in tags:
        tag = Tag.objects.filter(name=name, language="pl").first()
        if tag is None:
            tag = Tag.objects.create(name=name, language="pl", status="published", created_by=user)
        tag_objs.append(tag)
    ds.tags.set(tag_objs)
    if standard is not None:
        save_dataset_standard(ds, standard, revalidate=False)
    return ds, action


def ensure_file_resource(dataset, ext_ident, title, description, filename, content, fmt=None, position=1,
                         force=False):
    """Upload `content` as the resource's main file; re-upload only when it changed."""
    from mcod.resources.models import Resource, ResourceFile

    user = admin_user()
    res = Resource.raw.filter(dataset=dataset, ext_ident=ext_ident, is_removed=False).first()
    if res is not None and res.link and not res.is_link_internal:
        res.delete()  # kind changed (link -> file)
        res = None
    fields = dict(title=title, description=description, position=position, status="published",
                  data_date=timezone.now().date(), contains_protected_data=False, modified_by=user,
                  **FLAG_DEFAULTS)
    ext = (fmt or filename.rsplit(".", 1)[-1]).lower()
    upload = SimpleUploadedFile(filename, content, content_type=MIMETYPES.get(ext, "application/octet-stream"))
    if res is None:
        res = Resource.objects.create(dataset=dataset, ext_ident=ext_ident, created_by=user, **fields)
        ResourceFile.objects.create(resource=res, is_main=True, file=upload)  # portal validation + indexing
        return res, "created"
    # Existing resource: keep its status (automatic validation may have blocked it -> draft); only a
    # changed file is re-published and re-validated by the portal (DEC-015).
    fields.pop("status")
    for key, value in fields.items():
        setattr(res, key, value)
    res.save()
    main_file = ResourceFile.objects.filter(resource=res, is_main=True).first()
    old = None
    if main_file and main_file.file:
        try:
            with main_file.file.open("rb") as fh:
                old = content_digest(fh.read(), filename)
        except (OSError, ValueError):
            old = None
    if old == content_digest(content, filename) and not force:
        return res, "unchanged"
    if main_file:
        main_file.file = upload
        main_file.save()
    else:
        ResourceFile.objects.create(resource=res, is_main=True, file=upload)
    Resource.raw.filter(pk=res.pk).update(status="published")
    Resource.raw.get(pk=res.pk).revalidate()
    return res, "updated"


def ensure_api_resource(dataset, ext_ident, title, description, link, position=1):
    """Connected API: API-type link resource (the portal checks the link, no file analysis)."""
    from mcod.resources.models import Resource

    user = admin_user()
    res = Resource.raw.filter(dataset=dataset, ext_ident=ext_ident, is_removed=False).first()
    if res is not None and not res.link:
        res.delete()  # kind changed (file -> link)
        res = None
    fields = dict(title=title, description=description, position=position, status="published",
                  data_date=timezone.now().date(), contains_protected_data=False, modified_by=user,
                  forced_api_type=True, forced_file_type=False, **FLAG_DEFAULTS)
    if res is None:
        res = Resource.objects.create(dataset=dataset, ext_ident=ext_ident, link=link, created_by=user, **fields)
        return res, "created"
    link_changed = res.link != link
    res.link = link
    if not link_changed:
        fields.pop("status")  # keep a status set by automatic validation
    for key, value in fields.items():
        setattr(res, key, value)
    res.save()
    return res, "updated" if link_changed else "unchanged"


GEO_COLUMNS = {"label": "nazwa", "b": "szerokosc_geograficzna", "l": "dlugosc_geograficzna"}


def ensure_map_columns(resource_id):
    """Common CSV: all columns `string` (the portal guesses boolean/integer from the first rows and then
    rejects empty cells), coordinates `number`, map columns label/b/l; re-index when changed (T06 logic)."""
    from mcod.core.api.search.tasks import update_with_related_task
    from mcod.resources.models import Resource

    res = Resource.raw.get(pk=resource_id)
    tds = res.tabular_data_schema
    if not tds or not tds.get("fields"):
        return False
    wanted = {col: key for key, col in GEO_COLUMNS.items()}
    new_tds = dict(tds)
    new_tds["fields"], new_tds["geo"] = [], {}
    for idx, f in enumerate(tds["fields"]):
        f = {k: v for k, v in f.items() if k != "geo"}
        f["type"], f["format"] = "string", "default"
        key = wanted.get(f.get("name"))
        if key:
            f["geo"] = key
            if key in ("b", "l"):
                f["type"] = "number"
            new_tds["geo"][key] = {"col_name": f["name"], "col_index": idx}
        new_tds["fields"].append(f)
    if new_tds == tds and res.has_map:
        return False
    Resource.raw.filter(pk=resource_id).update(tabular_data_schema=new_tds)
    Resource.raw.get(pk=resource_id).revalidate_tabular_data(apply_on_commit=False)
    update_with_related_task.apply(args=("resources", "Resource", resource_id))
    update_with_related_task.apply(args=("datasets", "Dataset", res.dataset_id))
    return True

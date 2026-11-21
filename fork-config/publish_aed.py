# Publish the national AED dataset ("Misja AED") in the local dane.gov.pl fork (T06).
#
# Run (stdin into the fork's Django shell; idempotent, safe to re-run):
#   fork-config/publish.sh                       # wrapper, see README "Publish"
#   docker exec -i -e AED_BASE_URL=https://aed.mcod.local mcod-admin python manage.py shell < fork-config/publish_aed.py
#
# Env:
#   AED_BASE_URL      base URL of our app as seen from the fork (default https://aed.mcod.local)
#   AED_WAIT_SECONDS  how long to wait for Celery to download + index the CSV (default 600)
#   AED_REVALIDATE=1  re-upload + re-validate all resources even if the files did not change
#
# Phase 1: organization + dataset + 5 resources. CSV, XLSX, GeoJSON and the schema XLSX are
#          downloaded from our app and uploaded as the resource's main file (ResourceFile post_save queues the
#          fork's Celery file validation + tabular data indexing). Re-runs upload a new
#          file only when its sha256 changed (i.e. after a re-harvest in our app).
#          JSON is an API-type link resource to our live /api/exports/aed.json.
# Phase 2: wait for the CSV's tabular_data_schema, set map columns (label=nazwa,
#          b=szerokosc_geograficzna, l=dlugosc_geograficzna) and re-index the CSV data
#          so the portal's "Mapa" tab and /1.4/resources/{id}/geo work.
#
# Everything is wrapped in main(): `manage.py shell` exec()s stdin, where top-level
# names are not visible inside comprehensions/functions.


def main():
    import hashlib
    import io
    import os
    import time
    import zipfile

    import requests
    import urllib3
    from django.core.files.uploadedfile import SimpleUploadedFile

    from django.contrib.auth import get_user_model
    from django.utils import timezone

    from mcod.categories.models import Category
    from mcod.datasets.models import Dataset
    from mcod.organizations.models import Organization
    from mcod.core.api.search.tasks import update_with_related_task
    from mcod.resources.models import Resource, ResourceFile
    from mcod.tags.models import Tag

    urllib3.disable_warnings()
    base = os.environ.get("AED_BASE_URL", "https://aed.mcod.local").rstrip("/")
    wait_seconds = int(os.environ.get("AED_WAIT_SECONDS", "600"))
    force_revalidate = os.environ.get("AED_REVALIDATE") == "1"

    admin = get_user_model().objects.filter(is_superuser=True).order_by("id").first()
    if admin is None:
        raise SystemExit("No superuser in the fork DB (run fork-config/setup.sh first)")

    # --- organization -------------------------------------------------------------
    org = Organization.raw.filter(title="Misja AED", is_removed=False).first()
    org_fields = dict(
        description=(
            "Zespół hackathonowy HackNation 2026 – Misja AED. Publikuje ogólnopolski zbiór "
            "defibrylatorów AED scalony z danych jednostek publicznych z dane.gov.pl "
            "oraz OpenStreetMap, w jednym wzorcowym zakresie danych."
        ),
        institution_type="other",
        status="published",
        city="Bydgoszcz",
        postal_code="85-000",
        street="Gdańska",
        street_number="187",
        email="kontakt@misja-aed.example",
        tel="48000000000",
        website=base + "/",
        abbreviation="AED",
        regon="000000000",
        modified_by=admin,
    )
    if org is None:
        org = Organization.objects.create(title="Misja AED", created_by=admin, **org_fields)
        print(f"organization created: {org.id}")
    else:
        for k, v in org_fields.items():
            setattr(org, k, v)
        org.save()
        print(f"organization exists: {org.id}")

    # --- dataset ------------------------------------------------------------------
    title = "Defibrylatory AED – zbiór ogólnopolski"
    description = (
        "<p>Ogólnopolski zbiór lokalizacji defibrylatorów AED. Powstał przez automatyczne "
        "zebranie wszystkich zbiorów o AED opublikowanych na dane.gov.pl (gminy, powiaty, "
        "uczelnie, Lasy Państwowe, m.st. Warszawa) oraz danych OpenStreetMap, sprowadzenie ich "
        "do jednego <strong>wzorcowego zakresu danych AED</strong> i scalenie z usunięciem "
        "duplikatów. Każdy rekord ma identyfikator <code>id_aed</code> i wskazanie źródeł "
        "(<code>zrodlo</code>, <code>zrodlo_url</code>).</p>"
        f"<p>Wzorcowy zakres danych (schemat): {base}/api/schema-standard/aed-schema.xlsx. "
        f"API zgodne z dane.gov.pl: {base}/api/1.4/datasets/1.</p>"
        "<p><strong>Licencja:</strong> zbiór zawiera dane OpenStreetMap, dlatego całość "
        "udostępniana jest na licencji Open Database License (ODbL 1.0) – © współtwórcy "
        "OpenStreetMap oraz wskazani w kolumnie <code>zrodlo</code> dysponenci danych.</p>"
    )
    ds = Dataset.raw.filter(title=title, organization=org, is_removed=False).first()
    ds_fields = dict(
        notes=description,
        status="published",
        update_frequency="daily",
        url=base + "/",
        # The fork only knows CC licences (license_chosen); the real licence (ODbL 1.0,
        # DEC-012) is stated in the DB/copyright condition and in the description.
        license_condition_source=True,
        license_condition_db_or_copyrighted=(
            "Zbiór zawiera dane OpenStreetMap udostępniane na licencji Open Database License "
            "(ODbL 1.0, https://opendatacommons.org/licenses/odbl/1-0/). Wykorzystując zbiór "
            "należy wskazać źródło („© współtwórcy OpenStreetMap; Misja AED”) i udostępniać "
            "bazy pochodne na tej samej licencji."
        ),
        has_dynamic_data=False,
        has_high_value_data=False,
        has_high_value_data_from_ec_list=False,
        has_research_data=False,
        is_update_notification_enabled=False,
        modified_by=admin,
    )
    if ds is None:
        ds = Dataset.objects.create(title=title, organization=org, created_by=admin, **ds_fields)
        print(f"dataset created: {ds.id}")
    else:
        for k, v in ds_fields.items():
            setattr(ds, k, v)
        ds.save()
        print(f"dataset exists: {ds.id}")

    heal = Category.objects.filter(code="HEAL").order_by("id").first()
    if heal is not None:
        ds.categories.set([heal])
    tags = []
    for name in ("AED", "defibrylatory", "zdrowie", "ratownictwo"):
        tag = Tag.objects.filter(name=name, language="pl").first()
        if tag is None:
            tag = Tag.objects.create(name=name, language="pl", status="published", created_by=admin)
        tags.append(tag)
    ds.tags.set(tags)

    # --- resources (uploaded files) -------------------------------------------------
    # Upstream treats a resource whose link points outside the fork's own API as
    # "linked" (Resource.is_linked) and never offers table/map previews for it, so -
    # like an operator uploading files in the admin - we download our exports and
    # upload them as the resources' main files (pattern from mcod/resources/dga_utils.py).
    today = timezone.now().date()
    api_info = f"Aktualne dane na żywo: {base}/api/exports/ (API zgodne z dane.gov.pl: {base}/api/1.4/)."
    resources_spec = [
        dict(
            key="csv",
            title="Defibrylatory AED – Polska (CSV)",
            url=f"{base}/api/exports/aed.csv",
            filename="defibrylatory-aed-polska.csv",
            mimetype="text/csv",
            description="Pełny zbiór w formacie CSV (UTF-8, separator przecinek), kolumny "
            "zgodne ze wzorcowym zakresem danych AED. Podgląd tabeli i mapy. " + api_info,
        ),
        dict(
            key="xlsx",
            title="Defibrylatory AED – Polska (XLSX)",
            url=f"{base}/api/exports/aed.xlsx",
            filename="defibrylatory-aed-polska.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            description="Pełny zbiór w formacie arkusza XLSX, kolumny zgodne ze wzorcowym "
            "zakresem danych AED, z arkuszem metadanych. " + api_info,
        ),
        dict(
            key="geojson",
            title="Defibrylatory AED – Polska (GeoJSON)",
            url=f"{base}/api/exports/aed.geojson",
            filename="defibrylatory-aed-polska.geojson",
            mimetype="application/geo+json",
            description="Pełny zbiór jako GeoJSON FeatureCollection (WGS84) – gotowy do "
            "użycia w systemach mapowych i GIS. " + api_info,
        ),
        dict(
            # API-type link resource to our dane.gov.pl-compatible /1.4 data endpoint
            # (application/json, no attachment header -> the fork classifies it as "api").
            # Not a file upload: libmagic sees our 22 MB JSON export as text/plain and the
            # fork then tries every rdflib parser on it (minutes of Celery CPU per run).
            key="json",
            title="Defibrylatory AED – API zgodne z dane.gov.pl (JSON)",
            url=f"{base}/api/1.4/resources/1/data",
            api=True,
            description="Dane zbioru na żywo przez API Misji AED zgodne z API dane.gov.pl 1.4 "
            "(JSON:API, stronicowanie page/per_page, wyszukiwanie q). Pełny eksport JSON: "
            f"{base}/api/exports/aed.json. " + api_info,
        ),
        dict(
            key="schema",
            title="Wzorcowy zakres danych AED (schemat, XLSX)",
            url=f"{base}/api/schema-standard/aed-schema.xlsx",
            filename="wzorcowy-zakres-danych-aed.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            description="Specyfikacja wzorcowego zakresu danych o defibrylatorach AED: nazwy "
            "pól, typy, wymagalność, opisy i dozwolone wartości. Do publikacji danych AED "
            f"przez gminy i inne jednostki. Także jako JSON Schema: {base}/api/schema-standard/aed-schema.json.",
        ),
    ]
    by_key = {}
    def file_digest(data, filename):
        # XLSX files are zip archives with a creation timestamp in docProps/core.xml
        if filename.endswith(".xlsx"):
            h = hashlib.sha256()
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                for name in sorted(zf.namelist()):
                    if name != "docProps/core.xml":
                        h.update(name.encode())
                        h.update(zf.read(name))
            return h.hexdigest()
        return hashlib.sha256(data).hexdigest()

    for pos, spec in enumerate(resources_spec, 1):
        is_api = spec.get("api", False)
        res = Resource.raw.filter(dataset=ds, title=spec["title"], is_removed=False).first()
        if res is None and is_api:  # renamed in this script version
            res = Resource.raw.filter(
                dataset=ds, title__startswith="Defibrylatory AED – Polska (JSON", is_removed=False
            ).first()
        if res is not None:
            is_external_link = bool(res.link and not res.is_link_internal)
            if is_external_link != is_api:
                # kind changed (file upload <-> API link) -> replace the resource
                res.delete()
                print(f"resource {spec['key']}: removed resource {res.id} of the other kind")
                res = None
        fields = dict(
            title=spec["title"],
            description=spec["description"],
            position=pos,
            status="published",
            data_date=today,
            has_dynamic_data=is_api,
            has_high_value_data=False,
            has_high_value_data_from_ec_list=False,
            has_research_data=False,
            contains_protected_data=False,
            modified_by=admin,
        )

        if is_api:
            fields.update(forced_api_type=True, forced_file_type=False)
            if res is None:
                res = Resource.objects.create(
                    dataset=ds, link=spec["url"], created_by=admin, **fields
                )  # published + new link -> link validation only (type api, no file analysis)
                print(f"resource {spec['key']} created: {res.id} (API link {spec['url']})")
            else:
                res.link = spec["url"]
                for k, v in fields.items():
                    setattr(res, k, v)
                res.save()
                print(f"resource {spec['key']} exists: {res.id} (API link)")
            by_key[spec["key"]] = res
            continue

        resp = requests.get(spec["url"], timeout=300, verify=False)  # self-signed cert in the fork
        resp.raise_for_status()
        content = resp.content
        digest = file_digest(content, spec["filename"])
        upload = SimpleUploadedFile(spec["filename"], content, content_type=spec["mimetype"])
        if res is None:
            res = Resource.objects.create(dataset=ds, created_by=admin, **fields)
            Resource.raw.filter(pk=res.pk).update(data_tasks_last_status="")
            ResourceFile.objects.create(resource=res, is_main=True, file=upload)  # queues validation
            print(f"resource {spec['key']} created: {res.id} ({len(content)} B)")
        else:
            for k, v in fields.items():
                setattr(res, k, v)
            res.save()
            main_file = ResourceFile.objects.filter(resource=res, is_main=True).first()
            old_digest = None
            if main_file and main_file.file:
                try:
                    with main_file.file.open("rb") as fh:
                        old_digest = file_digest(fh.read(), spec["filename"])
                except (OSError, ValueError, zipfile.BadZipFile):
                    old_digest = None
            if old_digest == digest and not force_revalidate:
                print(f"resource {spec['key']} exists: {res.id} (file unchanged)")
            else:
                Resource.raw.filter(pk=res.pk).update(data_tasks_last_status="")
                if main_file:
                    main_file.file = upload
                    main_file.save()
                else:
                    ResourceFile.objects.create(resource=res, is_main=True, file=upload)
                Resource.raw.get(pk=res.pk).revalidate()
                print(f"resource {spec['key']} exists: {res.id} (new file uploaded, revalidation queued)")
        by_key[spec["key"]] = res

    # --- phase 2: map columns on the CSV --------------------------------------------
    csv_res = by_key["csv"]
    geo_cols = {"label": "nazwa", "b": "szerokosc_geograficzna", "l": "dlugosc_geograficzna"}
    deadline = time.time() + wait_seconds
    tds = None
    print(f"waiting up to {wait_seconds}s for Celery to download/parse the CSV ...")
    while time.time() < deadline:
        r = Resource.raw.get(pk=csv_res.pk)
        tds = r.tabular_data_schema
        if r.data_tasks_last_status in ("SUCCESS", "FAILURE") and tds and tds.get("fields"):
            break
        time.sleep(5)
    if not tds or not tds.get("fields"):
        print("CSV not processed yet - re-run this script later to set the map columns.")
        return

    names = [f.get("name") for f in tds["fields"]]
    missing = [c for c in geo_cols.values() if c not in names]
    if missing:
        print(f"CSV schema lacks columns {missing}; map not configured.")
        return

    # The fork guesses column types from the first rows (boolean/integer) and then
    # rejects empty cells, so every column is a string except the numeric coordinates.
    wanted = {}
    for key, col in geo_cols.items():
        wanted[col] = key
    new_tds = dict(tds)
    new_tds["fields"] = []
    new_tds["geo"] = {}
    for idx, f in enumerate(tds["fields"]):
        f = {k: v for k, v in f.items() if k != "geo"}
        f["type"] = "string"
        f["format"] = "default"
        key = wanted.get(f.get("name"))
        if key:
            f["geo"] = key
            if key in ("b", "l"):
                f["type"] = "number"
            new_tds["geo"][key] = {"col_name": f["name"], "col_index": idx}
        new_tds["fields"].append(f)

    if new_tds == tds and Resource.raw.get(pk=csv_res.pk).has_map and not force_revalidate:
        print("map columns already set, has_map=True")
    else:
        Resource.raw.filter(pk=csv_res.pk).update(tabular_data_schema=new_tds)
        r = Resource.raw.get(pk=csv_res.pk)
        print("map columns set; re-indexing CSV rows (synchronous, ~1 min) ...")
        r.revalidate_tabular_data(apply_on_commit=False)

    # has_table/has_map are written without signals after indexing -> refresh ES docs
    for res in by_key.values():
        update_with_related_task.apply(args=("resources", "Resource", res.pk))
    update_with_related_task.apply(args=("datasets", "Dataset", ds.pk))

    print("")
    print(f"DATASET {ds.id} {ds.slug}")
    for key, res in by_key.items():
        r = Resource.raw.get(pk=res.pk)
        print(
            f"RESOURCE {key:8} id={r.id} format={r.format} "
            f"file={r.file_tasks_last_status or '-'} "
            f"data={r.data_tasks_last_status or '-'} table={r.has_table} map={r.has_map}"
        )


main()

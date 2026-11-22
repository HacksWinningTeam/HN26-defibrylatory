# fork-config — local dane.gov.pl fork (T05)

Runs the upstream dane.gov.pl portal (`dane-gov-pl/backend_latest` = Django/Falcon "mcod",
`dane-gov-pl/frontend_latest` = Angular 18) locally. `dane-gov-pl/` is git-ignored upstream
code; **everything we change lives here** and is copied in by `setup.sh`.

## Files

| File | Purpose | Copied to |
|---|---|---|
| `backend.env` | upstream `env.sample` + `DISCOURSE_FORUM_ENABLED=false`, subnet 172.28.18.x, frontend -> `mcod-frontend` container | `backend_latest/.env` |
| `local.py` | upstream `local.py.sample` (INTERNAL_IPS subnet changed) | `backend_latest/mcod/settings/local.py` |
| `nginx/07-aed.conf.template` | https `aed.mcod.local` -> our Django on host `:8000` | `backend_latest/docker/nginx/config-templates/` |
| `compose.override.yml` | project `danegov-fork`, subnet 172.28.18.0/24, only 80/443 (+127.0.0.1:8025) published, no rdfdb/discourse deps, unused services disabled, `aed.mcod.local` alias, `mcod-frontend` (ng serve) service, app services use image `mcod-app:local` | used in place (`-f`) |
| `fork-compose.sh` | `docker compose -f docker-compose.local.yml -f compose.override.yml "$@"` run in `backend_latest/` | — |
| `setup.sh` / `start.sh` / `stop.sh` | idempotent setup; start; stop (never `-v`) | — |
| `publish_aed.py` / `publish.sh` | publish/refresh the national AED dataset in the fork (T06) | stdin of `manage.py shell` |
| `mcod_aed/` | the `mcod.aed` Django app (DEC-014) | bind-mounted at `mcod/aed` |
| `test.sh` | run the `mcod.aed` tests in `mcod-admin` | — |

`setup.sh` also creates empty dirs (bind-mount targets) `backend_latest/test-data`,
`frontend_latest/node_modules`, `frontend_latest/.angular` (the real `node_modules` lives in
the docker volume `danegov-fork_frontend_node_modules`). Nothing else in `dane-gov-pl/` is modified.
Note: the app containers run as root and write `backend_latest/media/` (fixture files).

## One-time steps (need sudo, do them yourself)

```bash
# 1. hostnames -> nginx published on 127.0.0.1:80/443
echo '127.0.0.1 mcod.local api.mcod.local admin.mcod.local cms.mcod.local aed.mcod.local' | sudo tee -a /etc/hosts
# 2. Elasticsearch needs vm.max_map_count >= 262144 (already 1048576 on this machine)
sysctl vm.max_map_count
```

Host ports 80 and 443 must be free (the fork's nginx takes them).

## Run

```bash
fork-config/setup.sh      # first time (builds, init DB + ES, starts everything)
fork-config/start.sh      # later / after reboot
fork-config/stop.sh       # stop (volumes kept)
fork-config/fork-compose.sh ps
fork-config/fork-compose.sh logs -f mcod-local-api
fork-config/fork-compose.sh run --rm --no-deps mcod-local-run python manage.py shell
```

**Always name services** with `fork-compose.sh up/build` (the override disables discourse
etc. via a profile, but be explicit anyway).

## `mcod.aed` plugin — data standards, validation, aggregation (DEC-014 / DEC-015)

A regular dane.gov.pl Django app living in **`fork-config/mcod_aed/`** (tracked). It is
**bind-mounted** at `backend_latest/mcod/aed` into every app container (`compose.override.yml`) and
enabled in `local.py` (`INSTALLED_APPS += ["mcod.aed.apps.AedConfig"]`). No upstream file is edited:
all hooks are applied from `AedConfig.ready()` (`integration.py`), scoped by the container's `COMPONENT`:

| Hook | Container | Effect |
|---|---|---|
| append `mcod.aed.views.ROUTES` (+ `/{api_version}` variants) to `mcod.routes.routes` | api | `/1.4/aed/schema`, `/1.4/aed/schema.xlsx`, `.csv` (template), `.json` (JSON Schema), `/1.4/aed/table-schema.json` |
| `data_standard` field on `DatasetApiAttrs` | api | `{code,name,version}` or `null` in `/1.4/datasets` and `/1.4/datasets/{id}` |
| wrap `DatasetAdminMixin.form` / `get_fieldsets` / `save_model` | admin | "Standard danych" select on the dataset *General* tab → `DatasetStandard` |

| wrap `ResourceForm.clean` | admin | publishing a resource of a standard dataset with blocking errors is refused (errors at the file field) |
| message on resource change page | admin | stored validation result (green / yellow / red "ZASÓB ZABLOKOWANY") |
| `task_postrun` of the portal's resource/file validation tasks → `mcod.aed.tasks.validate_resource_standard_task` | celery | every resource of a standard dataset is validated after processing; blocking → `draft` |

Import of the real sources (T12): `docker exec mcod-admin python manage.py aed_import_sources [--offline] [--no-osm] [--force]`
mirrors the AED datasets of dane.gov.pl (discovered via the public search API; snapshot fallback in `mcod_aed/fixtures/snapshot/`)
as datasets of their own institutions with "Standard danych" = aed-pl, plus OpenStreetMap; Warsaw and OSM are connected APIs.
`WARSAW_API_TOKEN` is read by `fork-compose.sh` from the repo's untracked `.env` (recreate admin/api/celery after changing it).
Legionowo's original file is blocked by validation; a corrected copy (`mcod_aed/fixtures/corrected/`) is published next to it (DEC-016).

Demo preparation (T09): `fork-config/aed-demo.sh [--offline]` = import + wait for validation + aggregation (~45 s). Script: `docs/demo-script.md`.

Aggregation (T13): `docker exec mcod-admin python manage.py aed_aggregate` or admin *Standardy danych* → "Uruchom agregację"
(Celery) → all published, non-blocked resources of `aed-pl` datasets → `AedSourceRecord` → merge → `AedDevice` → common dataset
"Defibrylatory AED – zbiór ogólnopolski" (CSV with Tabela/Mapa, XLSX, GeoJSON, schema, API link). API: `/1.4/aed/devices`
(GeoJSON, `bbox`, `q`), `/1.4/aed/sources` (per-source report). Datasets marked as demo must stay drafts (never aggregated).

Validation API (T14): `POST /1.4/aed/validate` (multipart `file`, raw body, or JSON `{"url"}` / `{"resource_id"}`; `?strict=true`), `GET` = help;
`GET /1.4/resources/{id}/standard-validation` = stored result. Samples: `docs/demo/samples/*.csv`.

Models: `DataStandard` (seeded `aed-pl` v1.0.0, `max_invalid_ratio` 0.2, admin *Standardy danych*),
`DatasetStandard`, `ResourceStandardValidation` (filled from T14). Code changes reload automatically in
api/admin; restart celery (`docker restart mcod-celery`). New migrations:
`fork-compose.sh run --rm --no-deps mcod-local-run python manage.py makemigrations aed` (files are created as root —
`docker run --rm -v $PWD/fork-config/mcod_aed:/x --entrypoint chown mcod-app:local -R 1000:1000 /x`), then
`docker exec mcod-admin python manage.py migrate aed`.

Tests (no pytest in the mcod image → `unittest`, against the live fork DB, writes rolled back):

```bash
fork-config/test.sh -v
```

## Publish the national AED dataset (T06)

Needs the fork running **and** our stack (`make up-d`, with harvested data), since the script
downloads our exports through `https://aed.mcod.local`.

```bash
fork-config/publish.sh                    # idempotent; prints dataset + resource ids and task states
AED_REVALIDATE=1 fork-config/publish.sh   # force re-upload + re-validation of every resource
AED_BASE_URL=https://aed.<host> fork-config/publish.sh   # another base URL (e.g. Hetzner, T10)
```

What it does (`publish_aed.py`, piped into `manage.py shell` of `mcod-admin`):

1. Organization **Misja AED**, dataset **Defibrylatory AED – zbiór ogólnopolski** (category Zdrowie/HEAL,
   tags AED/defibrylatory/zdrowie/ratownictwo, update frequency daily, ODbL note in the licence conditions).
2. Resources: CSV, XLSX, GeoJSON and the schema XLSX are **downloaded from our app and uploaded as files**
   (link resources pointing outside the fork are "linked" upstream and never get table/map previews);
   re-runs upload a new file only when the content changed. JSON is an **API** link resource to
   `/api/1.4/resources/1/data` (a 22 MB JSON file would make the fork's Celery try every RDF parser on it).
3. Waits for Celery to parse the CSV, sets all columns to `string` (coordinates `number`) and the map
   columns `label=nazwa`, `b=szerokosc_geograficzna`, `l=dlugosc_geograficzna`, re-indexes (~10 s) and
   refreshes the Elasticsearch documents.

After a re-harvest in our app just run `fork-config/publish.sh` again.

Check: `https://mcod.local/pl/dataset?q=defibrylatory` → dataset page → CSV resource → *Tabela* / *Mapa*;
`https://api.mcod.local/1.4/datasets?q=defibrylatory`, `https://api.mcod.local/1.4/resources/<csv id>/geo`.

**Manual fallback (admin, https://admin.mcod.local):** Instytucje → add "Misja AED"; Zbiory danych → add
dataset (institution, category Zdrowie, tags, licence conditions); Zasoby → add resource with the CSV file
(downloaded from `http://localhost:8000/api/exports/aed.csv`); after validation open the resource →
*Typy danych*: set every column to *string* except the coordinates (*number*), save; *Mapy i wykresy*: pick
*etykieta* = `nazwa`, *szerokość* = `szerokosc_geograficzna`, *długość* = `dlugosc_geograficzna`, save.

Known limitations: the XLSX resources have no table preview (typed cells + trailing empty column fail the
fork's goodtables check) — the CSV is the previewed resource. The fork's licence field only knows CC
licences, so the portal shows "CC BY 4.0"; the ODbL 1.0 requirement is in the conditions and description.

## Hetzner deployment for the judges (T10, DEC-018)

Public URLs (Let's Encrypt, no hosts edits): **https://mcod.2.29.205.102.sslip.io** (portal),
**https://admin.mcod.2.29.205.102.sslip.io** (admin), **https://api.mcod.2.29.205.102.sslip.io/1.4/** (API).
Server `ssh hack`, code in `/home/github/apps/danegov-fork/` (outside the CI-synced app dir; a push to `main`
never touches it). The fork's nginx publishes 80/443 on the server.

```bash
# 1. once: ship the fork images (built locally; ~6 GB raw, zstd-compressed)
docker save danegov-fork-mcod-db elasticsearch:6.8.23-mcod-1 mailhog/mailhog mcod-app:local nginx:1.31-mcod-1 \
  node:22-bookworm-slim rabbitmq:4.2.5-management-alpine-mcod redis:8.4.2-trixie-mcod | zstd -T0 -3 -c \
  | ssh hack 'zstd -d -c | docker load'
# 2. code + config + hostnames + certificate + setup (idempotent)
fork-config/hetzner/deploy.sh            # defaults: ssh host "hack", IP 2.29.205.102
# 3. data
ssh hack 'cd /home/github/apps/danegov-fork && fork-config/aed-demo.sh'
```

`hetzner/apply-hostnames.sh` rewrites `mcod.local` → `mcod.<ip>.sslip.io` in the **deployed copy only**
(backend `.env`, nginx templates, Angular proxy/allowedHosts, compose aliases; the fixture login
`admin@mcod.local` stays). `hetzner/certs.sh` gets a Let's Encrypt certificate with a one-off certbot
container on port 80 (no e-mail registered), falling back to self-signed. `setup.sh` honours `FORK_SKIP_BUILD=1`
(use the shipped images). `WARSAW_API_TOKEN` is copied from the repo `.env` into the server's `danegov-fork/.env`.

## URLs & credentials (accept the self-signed certificate once per hostname)

| URL | What |
|---|---|
| https://mcod.local | portal (Angular dev server in `mcod-frontend`, proxies `/api` -> api.mcod.local) |
| https://admin.mcod.local | Django admin — `admin@mcod.local` / `testadmin123!` |
| https://api.mcod.local/1.4/datasets | API |
| https://aed.mcod.local/api/health/ | our hackathon backend (host port 8000) through the fork nginx |
| http://127.0.0.1:8025 | MailHog |

Before the hosts line exists you can test with e.g.
`curl -k --resolve api.mcod.local:443:127.0.0.1 https://api.mcod.local/1.4/datasets`.
From inside the fork network: `docker exec mcod-celery curl -sk https://aed.mcod.local/api/health/`.

## Services

Used: `mcod-db`, `mcod-redis`, `mcod-rabbitmq`, `mcod-elasticsearch`, `mcod-smtp`, `mcod-nginx`,
`mcod-local-admin` (:8001), `mcod-local-api` (:8000), `mcod-local-cms` (:8002), `mcod-local-celery`,
`mcod-frontend` (:4200). None publish host ports except nginx 80/443 and mailhog 127.0.0.1:8025,
so our own stack (3000/8000/5432) runs alongside.
Disabled: discourse(+sidekiq) (private registry image), flower, rdfdb (`USE_RDF_DB` False), ws.

## Troubleshooting

- **Docker Hub `429 Too Many Requests`**: anonymous pull limit. `setup.sh` pre-pulls base images
  from `mirror.gcr.io` and re-tags them (`docker pull mirror.gcr.io/library/postgres:17-trixie && docker tag ... postgres:17-trixie`).
  Elasticsearch comes from docker.elastic.co (unaffected).
- **`Pool overlaps with other one on this address space`**: the upstream subnet 172.18.18.0/24
  collides with another docker network (`src_default` 172.18.0.0/16); the override uses 172.28.18.0/24.
  If that collides too, change the subnet + all `ipv4_address` in `compose.override.yml` and the IPs in `backend.env`.
- **502 on https://mcod.local**: Angular still compiling — `docker logs -f mcod-frontend`.
- **Empty *Mapa* tab** (`Dynamic require of "leaflet" is not supported` in the console): `ng serve` must run
  with `--prebundle=false` (set in `compose.override.yml`); recreate with `fork-compose.sh up -d mcod-frontend`.
- **Upstream package changes**: `mcod-frontend` re-runs `npm ci` when `package-lock.json` changes.
- **App image rebuild** (after changing Pipfile): `docker rmi mcod-app:local && fork-config/setup.sh`.
  Code changes in `backend_latest/mcod` need no rebuild (bind-mounted; api/admin auto-reload, restart celery).
- **aed.mcod.local returns 502**: our stack is not running (`make up-d`), or the host firewall blocks
  docker -> host:8000. nginx sends `Host: localhost` because our `DJANGO_ALLOWED_HOSTS` doesn't include aed.mcod.local.
- Admin `/media/resources/` is hard-coded upstream to `host.docker.internal:8001` (bare-metal setup) — file
  downloads via admin may 502; API/portal downloads go through api.mcod.local.

## Observed timings (this machine, 12 cores, 2026-11-21)

- App image `mcod-app:local` (python 3.8 + apt from snapshot.debian.org + pipenv): **23.5 min** (one-time, 3.4 GB)
- Infra images (postgres/redis/rabbitmq/ES/nginx) after mirror pre-pull: ~25 s
- `mcod-frontend` first start (`npm ci` + first `ng serve` compile): ~4 min; later starts ~1 min
- `init_mcod_db`: ~70 s; `search_index --rebuild -f`: ~25 s
- app services up and answering: ~40 s
- re-running `setup.sh` when everything exists: ~17 s
- Total from scratch: ~30 min, dominated by the app image build.

## Known noise / limitations

- Celery logs `update_graph_task ... Temporary failure in name resolution`: upstream fires RDF (Fuseki) tasks
  regardless of `USE_RDF_DB`; we don't run `mcod-rdfdb`. Harmless (no retry).
- Wagtail CMS is empty, so CMS-driven parts of the portal (privacy-policy modal text, footer, news) are blank.
- The self-signed cert covers mcod.local/api/admin/cms only; `aed.mcod.local` shows a name mismatch in a
  browser (the fork itself downloads with `verify=False`, so this does not matter for resource links).

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

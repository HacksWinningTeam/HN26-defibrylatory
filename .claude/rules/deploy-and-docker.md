---
paths:
  - "compose*.yaml"
  - "**/Dockerfile"
  - ".github/workflows/**"
  - "Makefile"
  - ".env.example"
---

# Deployment & Docker Guardrails

- **Automatic Hetzner CI/CD & manual pushes:** Pushes to `main` automatically trigger `.github/workflows/deploy.yml` on the self-hosted Hetzner runner (`docker compose -f compose.prod.yaml up -d --build --remove-orphans`). Never run `git push`; the user pushes manually.
- **Single open port per app (`3000–3100`):** In `compose.prod.yaml`, only `frontend` publishes a host port (`FRONTEND_PORT`, default `3000`). Keep `db` and `backend` internal to the Docker network with no `ports:` mapping in `compose.prod.yaml`.
- **Deploy sync safety:** Preserve `--exclude='.git' --exclude='.env'` and `.git` cleanup in `.github/workflows/deploy.yml` so read-only `.git/objects/*` files do not cause permission errors and the server's `.env` stays intact.
- **Container invariants:** Keep PostgreSQL 18 mounted at `/var/lib/postgresql`, the `uv` virtualenv at `/opt/venv`, non-root `prod` stages in both Dockerfiles, and `DJANGO_SECRET_KEY` required in `compose.prod.yaml`.
- **Env parity & validation:** Mirror any new environment variable in `.env.example`, `compose.yaml`, and `compose.prod.yaml`. Validate Compose edits with `docker compose config --quiet` and `DJANGO_SECRET_KEY=ci-check docker compose -f compose.prod.yaml config --quiet`.

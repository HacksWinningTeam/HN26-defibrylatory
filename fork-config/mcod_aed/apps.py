"""`mcod.aed` — data standards (AED first), validation and aggregation inside dane.gov.pl (DEC-014/015).

Installed into the fork by bind-mounting `fork-config/mcod_aed` at `mcod/aed` (compose.override.yml)
and listing it in `INSTALLED_APPS` (fork-config/local.py). All hooks into upstream code are applied
from `ready()` (see `integration.py`), so no upstream file is edited.
"""
from django.apps import AppConfig


class AedConfig(AppConfig):
    name = "mcod.aed"
    label = "aed"
    verbose_name = "Standardy danych (AED)"

    def ready(self):
        from mcod.aed import integration

        integration.install()

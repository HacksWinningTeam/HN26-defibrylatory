"""Application configuration for the AED (defibrillator) data app."""

from django.apps import AppConfig


class AedConfig(AppConfig):
    """Django AppConfig for AED schema, harvesting, merging and publishing."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.aed"
    verbose_name = "AED – defibrylatory"

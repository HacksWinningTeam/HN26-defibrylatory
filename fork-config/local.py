# fork-config/local.py -> dane-gov-pl/backend_latest/mcod/settings/local.py
# Upstream local.py.sample with: INTERNAL_IPS subnet 172.28.18.x; "timeout" removed from the
# ES index settings (ES 6.8 rejects unknown setting [index.timeout] on search_index --rebuild).
from mcod.settings.base import *  # noqa: F403

DEBUG = True

# DEC-014: AED data standard / validation / aggregation plugin (fork-config/mcod_aed)
INSTALLED_APPS = [*INSTALLED_APPS, "mcod.aed.apps.AedConfig"]  # noqa: F405
# Sidebar entry for the plugin (django-suit menu is an explicit list in base.py), right after "Dane".
SUIT_CONFIG["MENU"].insert(  # noqa: F405
    1,
    {
        "label": "Standardy danych",
        "icon": "icon-file",
        "models": [
            {"model": "aed.datastandard", "label": "Standardy danych (agregacja)"},
            {"model": "aed.aedimportrun", "label": "Agregacje AED"},
            {"model": "aed.aeddevice", "label": "Zbiór zbiorczy AED – urządzenia"},
            {"model": "aed.resourcestandardvalidation", "label": "Walidacje zasobów"},
            {"model": "aed.datasetstandard", "label": "Zbiory w standardach"},
            {"model": "aed.aedsourcerecord", "label": "Rekordy źródłowe"},
        ],
    },
)
ALLOWED_HOSTS = ["*"]

TEMPLATES[0]["OPTIONS"]["debug"] = DEBUG  # noqa: F405
INTERNAL_IPS = (
    "127.0.0.1",
    "localhost",
    "172.28.18.100",
)  # needed to use debug processor in django templates


if EMAIL_HOST:  # noqa: F405
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=False)
else:
    EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
    EMAIL_FILE_PATH = "/tmp/app-messages"

NO_REPLY_EMAIL = "no-reply@mcod.local"

ELASTICSEARCH_DSL_INDEX_SETTINGS = {
    "number_of_shards": 1,
    "number_of_replicas": 0,
}

ELASTICSEARCH_HISTORIES_IDX_SETTINGS = {
    "number_of_shards": 1,
    "number_of_replicas": 0,
}

CELERY_TASK_ALWAYS_EAGER = False

FIXTURE_DIRS = [
    str(ROOT_DIR("test-data/fixtures")),
]

MEDIA_ROOT = str(ROOT_DIR("media"))
ACADEMY_MEDIA_ROOT = str(ROOT_DIR.path(MEDIA_ROOT, "academy"))
IMAGES_MEDIA_ROOT = str(ROOT_DIR.path(MEDIA_ROOT, "images"))
LABORATORY_MEDIA_ROOT = str(ROOT_DIR.path(MEDIA_ROOT, "lab_reports"))
MEETINGS_MEDIA_ROOT = str(ROOT_DIR.path(MEDIA_ROOT, "meetings"))
NEWSLETTER_MEDIA_ROOT = str(ROOT_DIR.path(MEDIA_ROOT, "newsletter"))
RESOURCES_FILES_TO_REMOVE_ROOT = str(
    ROOT_DIR.path(MEDIA_ROOT, "to_be_removed", "resources")
)
RESOURCES_MEDIA_ROOT = str(ROOT_DIR.path(MEDIA_ROOT, "resources"))
SHOWCASES_MEDIA_ROOT = str(ROOT_DIR.path(MEDIA_ROOT, "showcases"))

SESSION_COOKIE_NAME = "local_sessionid"
# from the environment so the public deployment (sslip.io hostnames, T10) gets a matching cookie domain
SESSION_COOKIE_DOMAIN = env("SESSION_COOKIE_DOMAIN", default="mcod.local")  # noqa: F405
# mcod.aed: a source file that passes its standard refreshes the common dataset automatically (DEC-020)
AED_AUTO_AGGREGATION = env.bool("AED_AUTO_AGGREGATION", default=True)  # noqa: F405
SESSION_COOKIE_SECURE = False
API_TOKEN_COOKIE_NAME = "local_apiauthtoken"


LOGGING["loggers"]["django.db.backends"]["level"] = "ERROR"
LOGGING["loggers"]["django.db.backends"]["handlers"] = ["console"]
LOGGING["loggers"]["django.request"]["level"] = "DEBUG"
LOGGING["loggers"]["django.request"]["handlers"] = ["console"]
LOGGING["loggers"]["django.server"]["level"] = "DEBUG"
LOGGING["loggers"]["django.server"]["handlers"] = ["console"]
LOGGING["loggers"]["signals"]["level"] = "DEBUG"
LOGGING["loggers"]["signals"]["handlers"] = ["signals-console-handler"]
LOGGING["loggers"]["celery.app.trace"]["level"] = "WARNING"
LOGGING["loggers"]["celery.app.trace"]["handlers"] = ["console"]
LOGGING["loggers"]["mcod"]["handlers"] = ["console"]
LOGGING["loggers"]["resource_file_processing"]["handlers"] = ["console"]
LOGGING['loggers']['mcod-api']['level'] = 'DEBUG'

COMPONENT = env("COMPONENT", default="admin")
ENVIRONMENT = "local"

AXES_ENABLED=False

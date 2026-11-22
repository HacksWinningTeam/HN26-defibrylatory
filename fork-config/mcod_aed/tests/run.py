"""Run the mcod.aed test suite inside a fork app container (no pytest in the mcod image):
    docker exec mcod-admin python -m mcod.aed.tests.run [-v]
"""
import os
import sys
import unittest

import django


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mcod.settings.local")
    django.setup()
    here = os.path.dirname(os.path.abspath(__file__))
    suite = unittest.defaultTestLoader.discover(here, pattern="test_*.py", top_level_dir=os.path.dirname(os.path.dirname(os.path.dirname(here))))
    verbosity = 2 if "-v" in sys.argv else 1
    result = unittest.TextTestRunner(verbosity=verbosity).run(suite)
    sys.stdout.flush()
    os._exit(0 if result.wasSuccessful() else 1)  # skip background threads (API health monitor)


if __name__ == "__main__":
    main()

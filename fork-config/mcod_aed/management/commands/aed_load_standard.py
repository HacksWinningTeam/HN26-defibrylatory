"""manage.py aed_load_standard <file.json> [...] — create/update data-defined standards (DEC-019, T16)."""
import json

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Load data standard definitions (JSON) into the portal; the AED standard is refreshed from code."

    def add_arguments(self, parser):
        parser.add_argument("files", nargs="*", help="standard JSON files (default: all in mcod/aed/standards/)")

    def handle(self, *args, **options):
        import glob
        import os

        from mcod.aed.spec import StandardDefinitionError
        from mcod.aed.standards import STANDARDS_DIR, ensure_aed_standard, load_standard

        aed = ensure_aed_standard()
        self.stdout.write("aed-pl: {} pól (z kodu, schema.py)".format(len(aed.fields)))
        files = options["files"] or sorted(glob.glob(os.path.join(STANDARDS_DIR, "*.json")))
        for path in files:
            try:
                with open(path, encoding="utf-8") as fh:
                    standard, created = load_standard(json.load(fh))
            except (OSError, ValueError, StandardDefinitionError) as exc:
                raise CommandError("{}: {}".format(path, exc))
            self.stdout.write(self.style.SUCCESS("{} {}: {} – {} pól, wymagane: {}".format(
                "utworzono" if created else "zaktualizowano", standard.code, standard.name,
                len(standard.fields), ", ".join(standard.spec().required))))

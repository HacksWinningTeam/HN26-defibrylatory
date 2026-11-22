"""manage.py aed_import_sources [--offline] [--no-osm] [--force] — mirror AED sources into the portal (T12)."""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Mirror the AED datasets of dane.gov.pl (+ OpenStreetMap) into this portal, standard aed-pl."

    def add_arguments(self, parser):
        parser.add_argument("--offline", action="store_true", help="use the committed snapshot instead of dane.gov.pl")
        parser.add_argument("--no-osm", action="store_true", help="skip the OpenStreetMap connected API dataset")
        parser.add_argument("--force", action="store_true", help="re-upload files even if unchanged")

    def handle(self, *args, **options):
        from mcod.aed.importer import run_import

        report = run_import(offline=options["offline"], include_osm=not options["no_osm"], force=options["force"])
        self.stdout.write("Tryb: {}".format(report.mode))
        self.stdout.write("{:<45} {:>6}  {:<55} {:>7}  {:<10} {}".format(
            "Instytucja", "zbiór", "tytuł", "zasób", "rodzaj", "akcja"))
        for org, ds_id, ds_title, res_id, kind, action in report.rows:
            self.stdout.write("{:<45} {:>6}  {:<55} {:>7}  {:<10} {}".format(
                org[:45], ds_id, ds_title[:55], res_id, kind, action))
        for error in report.errors:
            self.stdout.write(self.style.WARNING("! " + error))
        self.stdout.write(self.style.SUCCESS("Gotowe: {} zbiorów, {} zasobów (standard aed-pl).".format(len({r[1] for r in report.rows}), len(report.rows))))

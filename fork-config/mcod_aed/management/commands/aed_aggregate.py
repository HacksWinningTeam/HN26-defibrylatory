"""manage.py aed_aggregate [--no-publish] — build the common AED dataset inside the portal (T13)."""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Aggregate all datasets with 'Standard danych' = aed-pl into 'Defibrylatory AED – zbiór ogólnopolski'."

    def add_arguments(self, parser):
        parser.add_argument("--no-publish", action="store_true", help="only rebuild records/devices, do not publish files")
        parser.add_argument("--standard", default="aed-pl", help="data standard code (default aed-pl)")

    def handle(self, *args, **options):
        from mcod.aed.aggregate import run_aggregation

        from mcod.aed.models import DataStandard

        standard = DataStandard.objects.get(code=options["standard"])
        run = run_aggregation(triggered_by="manage.py aed_aggregate", publish=not options["no_publish"], standard=standard)
        report = run.report
        self.stdout.write("{:<6} {:<48} {:<5} {:<9} {:>7} {:>8} {:>8}  {}".format(
            "zbiór", "źródło", "typ", "walidacja", "wiersze", "przyjęte", "pominięte", "pokrycie wymaganych"))
        for s in report["sources"]:
            self.stdout.write("{:<6} {:<48} {:<5} {:<9} {:>7} {:>8} {:>8}  {}".format(
                s["dataset_id"], (s["institution"] or s["dataset_title"])[:48], s["kind"],
                s.get("validation_status", s["status"]), s.get("rows", 0), s.get("records", 0),
                s.get("excluded_rows", 0), (s.get("coverage") or {}).get("required", "-")))
        for s in report["sources"]:
            if s.get("note") or s.get("error"):
                self.stdout.write(self.style.WARNING("! {}: {}".format(s["institution"] or s["dataset_title"], s.get("note") or s.get("error"))))
        self.stdout.write(self.style.SUCCESS(
            "Agregacja {} ({}): {} źródeł, {} rekordów ({} przyjętych) -> {} obiektów ({} z kilku źródeł).".format(
                run.pk, standard.code, run.sources_count, report["records"], report["records_included"],
                report["devices"], report["multi_source_devices"])))
        national = report.get("national_dataset")
        if national:
            self.stdout.write("Zbiór zbiorczy: {} ({})".format(national["title"], national["url"]))
            for ext, info in national["resources"].items():
                self.stdout.write("  {:<22} zasób {} {}".format(ext, info["resource_id"], info["action"]))

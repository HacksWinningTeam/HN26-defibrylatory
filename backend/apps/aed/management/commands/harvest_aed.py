"""Harvest AED sources from dane.gov.pl and OpenStreetMap (T02; parsing/merge added in T03)."""

from django.core.management.base import BaseCommand

from apps.aed import harvest
from apps.aed.models import SourceDataset


class Command(BaseCommand):
    help = "Discover and download all AED datasets from dane.gov.pl and OSM."

    def add_arguments(self, parser):
        parser.add_argument("--fetch-only", action="store_true", help="Only download raw data")
        parser.add_argument("--offline", action="store_true", help="Load the committed snapshot")
        parser.add_argument("--no-osm", action="store_true", help="Skip OpenStreetMap")
        parser.add_argument(
            "--save-snapshot", action="store_true", help="Write raw payloads to the snapshot dir"
        )

    def handle(self, *args, **options):
        if options["offline"]:
            report = harvest.load_snapshot()
            self.stdout.write(self.style.WARNING("Loaded OFFLINE snapshot (demo fallback)."))
        else:
            report = harvest.harvest_all(include_osm=not options["no_osm"])
        for error in report.errors:
            self.stdout.write(self.style.ERROR(error))

        self.stdout.write(f"{'source':<12} {'dataset':<62} {'fmt':<8} {'status':<22} {'bytes':>9}")
        for dataset in SourceDataset.objects.prefetch_related("resources"):
            for res in dataset.resources.all():
                mark = "*" if res.selected else " "
                self.stdout.write(
                    f"{dataset.kind:<12} {dataset.title[:60]:<62} {res.format:<8} "
                    f"{res.fetch_status:<22} {res.size:>9} {mark}"
                )
        self.stdout.write("(* = selected resource used for parsing)")
        if options["save_snapshot"]:
            count = harvest.save_snapshot()
            self.stdout.write(self.style.SUCCESS(f"Snapshot saved ({count} datasets)."))

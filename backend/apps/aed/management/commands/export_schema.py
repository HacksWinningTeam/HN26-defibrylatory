"""Write the standard AED schema artefacts to a directory (submission deliverables)."""

import json
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.aed import schema_export


class Command(BaseCommand):
    help = "Export the standard AED schema as xlsx, CSV template, JSON Schema and Table Schema."

    def add_arguments(self, parser):
        parser.add_argument("--out", default="exports/schema", help="Output directory")

    def handle(self, *args, **options):
        out = Path(options["out"])
        out.mkdir(parents=True, exist_ok=True)
        files = {
            "aed-schema.xlsx": schema_export.xlsx_bytes(),
            "aed-template.csv": ("﻿" + schema_export.csv_template()).encode("utf-8"),
            "aed-schema.json": json.dumps(
                schema_export.json_schema(), ensure_ascii=False, indent=2
            ).encode("utf-8"),
            "table-schema.json": json.dumps(
                schema_export.table_schema(), ensure_ascii=False, indent=2
            ).encode("utf-8"),
        }
        for name, content in files.items():
            (out / name).write_bytes(content)
            self.stdout.write(f"wrote {out / name} ({len(content)} B)")

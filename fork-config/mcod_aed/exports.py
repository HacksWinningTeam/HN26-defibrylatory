"""Files of the common AED dataset generated inside the portal (T13): CSV, XLSX, GeoJSON."""
import csv
import io
import json

from openpyxl import Workbook
from openpyxl.styles import Font

from mcod.aed.schema import FIELD_NAMES, SCHEMA_NAME, SCHEMA_VERSION

LICENSE = (
    "ODbL 1.0 – zbiór zawiera dane OpenStreetMap (© współtwórcy OpenStreetMap); dane instytucji: "
    "CC0 1.0 / CC BY 4.0 zgodnie z licencjami zbiorów źródłowych."
)


def cell(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return value


def csv_bytes(devices):
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(FIELD_NAMES)
    for device in devices:
        writer.writerow([cell(device.data.get(name)) for name in FIELD_NAMES])
    return out.getvalue().encode("utf-8")


def xlsx_bytes(devices, meta):
    wb = Workbook()
    ws = wb.active
    ws.title = "Dane"
    ws.append(list(FIELD_NAMES))
    for c in ws[1]:
        c.font = Font(bold=True)
    for device in devices:
        ws.append([cell(device.data.get(name)) for name in FIELD_NAMES])
    info = wb.create_sheet("Metadane")
    for key, value in meta.items():
        info.append([key, str(value)])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def geojson_bytes(devices, meta):
    features = [
        {
            "type": "Feature",
            "id": device.id_aed,
            "geometry": {"type": "Point", "coordinates": [device.lon, device.lat]},
            "properties": {name: device.data.get(name) for name in FIELD_NAMES if device.data.get(name) not in (None, "")},
        }
        for device in devices
    ]
    body = {"type": "FeatureCollection", "metadata": meta, "features": features}
    return json.dumps(body, ensure_ascii=False).encode("utf-8")


def metadata(run, devices_count):
    return {
        "tytul": "Defibrylatory AED – zbiór ogólnopolski",
        "standard": "{} v{}".format(SCHEMA_NAME, SCHEMA_VERSION),
        "liczba_urzadzen": devices_count,
        "agregacja": run.started_at.strftime("%Y-%m-%dT%H:%M:%SZ") if run and run.started_at else "",
        "licencja": LICENSE,
    }


def generic_csv_bytes(devices, names):
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(names)
    for device in devices:
        writer.writerow([cell(device.data.get(name)) for name in names])
    return out.getvalue().encode("utf-8")


def generic_xlsx_bytes(devices, names, meta):
    wb = Workbook()
    ws = wb.active
    ws.title = "Dane"
    ws.append(list(names))
    for c in ws[1]:
        c.font = Font(bold=True)
    for device in devices:
        ws.append([cell(device.data.get(name)) for name in names])
    info = wb.create_sheet("Metadane")
    for key, value in meta.items():
        info.append([key, str(value)])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()

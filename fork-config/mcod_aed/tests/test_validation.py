"""Validation of data against the AED standard (T14, DEC-015)."""
import io
import json
import os
import unittest

from openpyxl import Workbook

from mcod.aed import validation
from mcod.aed.schema import FIELD_NAMES

SAMPLES = os.path.join(os.path.dirname(__file__), "samples")
KROSNO = (
    "Długość geograficzna,Szerokość geograficzna, Nazwa, Lokalizacja, Adres, Numer Id\r\n"
    '21.72034402175176,49.718809346153336,"Defibrylator","Zespół  Krytych Pływalni",'
    '"ul. Jasna, 38-400 Krosno","1"\r\n'
).encode()


def sample(name):
    with open(os.path.join(SAMPLES, name), "rb") as fh:
        return fh.read()


def codes(report):
    return {(e["field"], e["code"]) for e in report["errors"]}


class ValidatorTests(unittest.TestCase):
    def test_valid_template_file(self):
        report = validation.validate_bytes(sample("aed-bydgoszcz-demo.csv"), filename="a.csv")
        self.assertEqual((report["status"], report["valid"], report["blocking"]), ("valid", True, False))
        self.assertEqual((report["rows_total"], report["rows_invalid"], report["errors"]), (3, 0, []))
        self.assertEqual(report["missing_required_fields"], [])
        self.assertTrue(all(info["match"] == "exact" for info in report["column_mapping"].values()))

    def test_invalid_file_errors_and_blocking(self):
        report = validation.validate_bytes(sample("aed-invalid-demo.csv"), filename="bad.csv")
        self.assertEqual((report["status"], report["valid"], report["blocking"]), ("invalid", False, True))
        self.assertEqual(report["rows_invalid"], 3)
        self.assertEqual(codes(report), {
            ("szerokosc_geograficzna", "coordinates_missing"),
            ("dostep", "allowed_values"),
            ("data_aktualizacji", "type_date"),
            ("szerokosc_geograficzna", "coordinates_outside_poland"),
            ("nazwa", "required"),
        })
        first = report["errors"][0]
        self.assertEqual(set(first), {"row", "field", "code", "message", "value"})
        self.assertTrue(report["blocking_reasons"])

    def test_legacy_source_is_mapped_with_warnings_not_blocked(self):
        report = validation.validate_bytes(KROSNO, filename="krosno.csv")
        self.assertEqual((report["status"], report["valid"], report["blocking"]), ("warnings", False, False))
        mapping = report["column_mapping"]
        self.assertEqual(mapping["Numer Id"], {"field": "id_aed", "match": "synonym"})
        self.assertEqual(mapping["Adres"]["match"], "address")
        warning_codes = {w["code"] for w in report["warnings"]}
        self.assertIn("required_derived", warning_codes)
        self.assertIn("column_synonym", warning_codes)
        self.assertGreater(report["coverage"]["required"], 0)

    def test_strict_mode_requires_standard_columns(self):
        report = validation.validate_bytes(KROSNO, filename="krosno.csv", strict=True)
        self.assertTrue(report["blocking"])
        self.assertIn("dostep", report["missing_required_fields"])
        self.assertIn("id_aed", report["missing_required_fields"])

    def test_invalid_ratio_threshold(self):
        header = "id_aed,nazwa,szerokosc_geograficzna,dlugosc_geograficzna,miejscowosc,dostep,zrodlo,data_aktualizacji\n"
        good = "A{i},AED {i},52.2,21.0,Warszawa,publiczny,test,2026-11-22\n"
        bad = "B{i},AED {i},,,Warszawa,publiczny,test,2026-11-22\n"
        body = header + "".join(good.format(i=i) for i in range(9)) + bad.format(i=1)
        report = validation.validate_bytes(body.encode(), filename="x.csv")  # 10% invalid
        self.assertFalse(report["blocking"])
        self.assertEqual(report["status"], "invalid" if report["blocking"] else "warnings")
        report = validation.validate_bytes(body.encode(), filename="x.csv", max_invalid_ratio=0.05)
        self.assertTrue(report["blocking"])

    def test_missing_town_is_warning_and_duplicate_id_is_error(self):
        body = ("id_aed,nazwa,szerokosc_geograficzna,dlugosc_geograficzna,miejscowosc,dostep,zrodlo,data_aktualizacji\n"
                "X1,AED,52.2,21.0,,publiczny,t,2026-11-22\nX1,AED 2,52.3,21.1,Warszawa,publiczny,t,2026-11-22\n")
        report = validation.validate_bytes(body.encode(), filename="x.csv")
        self.assertEqual(codes(report), {("id_aed", "duplicate_id")})
        self.assertIn("town_missing", {w["code"] for w in report["warnings"]})

    def test_type_checks(self):
        body = ("id_aed,nazwa,szerokosc_geograficzna,dlugosc_geograficzna,miejscowosc,dostep,zrodlo,data_aktualizacji,w_budynku,pietro,kod_pocztowy\n"
                "X1,AED,52.2,21.0,W,publiczny,t,2026-11-22,może,parter,00000\n")
        report = validation.validate_bytes(body.encode(), filename="x.csv")
        self.assertEqual(codes(report), {("w_budynku", "type_boolean"), ("pietro", "type_integer"), ("kod_pocztowy", "pattern")})

    def test_xlsx_json_geojson(self):
        wb = Workbook()
        wb.active.append(list(FIELD_NAMES[:4]) + ["miejscowosc"])
        wb.active.append(["X1", "AED", 52.2, 21.0, "Warszawa"])
        buf = io.BytesIO()
        wb.save(buf)
        report = validation.validate_bytes(buf.getvalue())
        self.assertEqual((report["format"], report["rows_total"], report["rows_invalid"]), ("xlsx", 1, 0))
        geo = json.dumps({"type": "FeatureCollection", "features": [{"type": "Feature",
              "geometry": {"type": "Point", "coordinates": [21.0, 52.2]}, "properties": {"nazwa": "AED"}}]}).encode()
        report = validation.validate_bytes(geo)
        self.assertEqual((report["format"], report["rows_invalid"]), ("geojson", 0))
        self.assertIn("(geometria)", report["column_mapping"])
        report = validation.validate_bytes(json.dumps([{"nazwa": "AED", "lat": "52.2", "lon": "21.0"}]).encode())
        self.assertEqual((report["format"], report["rows_total"], report["rows_invalid"]), ("json", 1, 0))

    def test_unreadable_and_empty_input(self):
        with self.assertRaises(validation.ValidationInputError):
            validation.validate_bytes(b"")
        with self.assertRaises(validation.ValidationInputError):
            validation.validate_bytes(b"\x00\x01garbage")
        report = validation.validate_bytes(b"nazwa,miejscowosc\n", filename="x.csv")
        self.assertTrue(report["blocking"])
        self.assertEqual(report["rows_total"], 0)

    def test_detect_format(self):
        self.assertEqual(validation.detect_format(b"a,b", filename="x.CSV"), "csv")
        self.assertEqual(validation.detect_format(b'{"type": "FeatureCollection"}'), "geojson")
        self.assertEqual(validation.detect_format(b"[{}]"), "json")
        self.assertEqual(validation.detect_format(b"<root/>"), "xml")
        self.assertEqual(validation.detect_format(b"x", hint="XLSX"), "xlsx")


if __name__ == "__main__":
    unittest.main()

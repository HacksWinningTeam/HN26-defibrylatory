"""Parsers + normalisation (ported from backend/apps/aed/tests/test_normalize_merge.py)."""
import io
import json
import unittest
from datetime import date

from openpyxl import Workbook

from mcod.aed import normalize, parsers

KROSNO = (
    "Długość geograficzna,Szerokość geograficzna, Nazwa, Lokalizacja, Adres, Numer Id\r\n"
    '21.72034402175176,49.718809346153336,"Defibrylator","Zespół  Krytych Pływalni",'
    '"ul. Jasna, 38-400 Krosno","1"\r\n'
).encode()
MARKI = (
    '"Długość geograficzna,Szerokość geograficzna, Nazwa, Lokalizacja, Adres, Numer Id"\r\n'
    '"52.326697, 21.107557,""Defibrylator"",""Urząd Miasta Marki "",'
    '""Al.. Piłsudskiego 95, 05-270 Marki"",""1"""\r\n'
).encode()
LEGIONOWO = (
    "﻿nazwa,cecha_ulicy,nazwa_ulicy,nr_budynku,nr_lokalu,kod_pocztowy,miejscowosc,"
    "kod_terc,kod_simc,szerokosc_geograficzna,dlugosc_geograficzna\r\n"
    "Urząd Miasta Legionowo,ulica,Piłsudskiego,41,,05-120,Legionowo,140801,0920806,"
    "52.395198,20.931382\r\n"
).encode()
WARSAW = json.dumps([{
    "geometry": {"coordinates": [[21.0148748, 52.2086170]], "type": "Point"},
    "properties": {
        "defibrillator_id": "622", "device_access_description": "Pn-Pt 8-16",
        "device_availability": "Ograniczona", "device_location": "Wewnątrz budynku",
        "device_manufacturer": "Medtronic", "device_public_access": "Publiczny",
        "location_building": "25/27", "location_city": "Warszawa",
        "location_description": "Przy wejściu na półpiętrze.",
        "location_object_name": "Urząd Dzielnicy Mokotów", "location_postcode": "02-517",
        "location_street": "Rakowiecka",
    },
}]).encode()
OSM = json.dumps({"type": "FeatureCollection", "features": [{
    "type": "Feature", "geometry": {"type": "Point", "coordinates": [21.01488, 52.20863]},
    "properties": {"@osm_id": 42, "@osm_type": "node", "emergency": "defibrillator",
                   "access": "customers", "indoor": "yes", "level": "1",
                   "opening_hours": "24/7", "operator": "Urząd Dzielnicy Mokotów",
                   "defibrillator:location:pl": "hol", "check_date": "2025-06-01"},
}]}).encode()

CTX = normalize.SourceContext(
    kind="dane_gov_pl", key="dgp1", name="Gmina", url="https://dane.gov.pl/pl/dataset/1",
    updated=date(2026, 1, 2),
)


class ParserTests(unittest.TestCase):
    def test_krosno_csv(self):
        rows = parsers.parse("csv", KROSNO)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].props["Lokalizacja"], "Zespół  Krytych Pływalni")

    def test_marki_row_wrapped_csv(self):
        rows = parsers.parse("csv", MARKI)
        self.assertEqual(rows[0].props["Adres"], "Al.. Piłsudskiego 95, 05-270 Marki")

    def test_semicolon_csv(self):
        rows = parsers.parse("csv", "id;name;city\n744;AED ADM;Przemyśl\n".encode())
        self.assertEqual(rows[0].props, {"id": "744", "name": "AED ADM", "city": "Przemyśl"})

    def test_xlsx(self):
        wb = Workbook()
        wb.active.append(["nazwa", "szerokosc_geograficzna", "dlugosc_geograficzna"])
        wb.active.append(["Urząd", 52.1, 21.0])
        buf = io.BytesIO()
        wb.save(buf)
        row = parsers.parse("xlsx", buf.getvalue())[0]
        self.assertEqual((row.props["nazwa"], row.props["szerokosc_geograficzna"]), ("Urząd", "52.1"))

    def test_warsaw_nested_coordinates(self):
        row = parsers.parse("json", WARSAW)[0]
        self.assertEqual((row.lon, row.lat, row.row_id), (21.0148748, 52.2086170, "622"))

    def test_unknown_format_raises(self):
        with self.assertRaises(parsers.ParseError):
            parsers.parse("gml", b"<gml/>")


class NormalizeTests(unittest.TestCase):
    def test_parse_address(self):
        self.assertEqual(normalize.parse_address("ul. Stanisława Wyspiańskiego 20, 38-400 Krosno"), {
            "kod_pocztowy": "38-400", "miejscowosc": "Krosno", "cecha_ulicy": "ul.",
            "nazwa_ulicy": "Stanisława Wyspiańskiego", "nr_budynku": "20",
        })

    def test_krosno(self):
        result = normalize.normalize_row(parsers.parse("csv", KROSNO)[0], CTX)
        self.assertTrue(result.valid)
        self.assertEqual(result.data["nazwa"], "Zespół Krytych Pływalni")
        self.assertEqual(result.data["miejscowosc"], "Krosno")
        self.assertEqual(result.data["id_aed"], "dgp1-1")

    def test_marki_swapped_coordinates(self):
        result = normalize.normalize_row(parsers.parse("csv", MARKI)[0], CTX)
        self.assertIn("wspolrzedne_zamienione", result.flags)
        self.assertEqual((result.lat, result.lon), (52.326697, 21.107557))

    def test_legionowo_teryt(self):
        result = normalize.normalize_row(parsers.parse("csv", LEGIONOWO)[0], CTX)
        self.assertEqual(result.data["cecha_ulicy"], "ul.")
        self.assertIn("kod_terc_niepoprawny", result.flags)

    def test_osm_tags(self):
        ctx = normalize.SourceContext("osm", "osm", "OpenStreetMap", "https://osm.org", None)
        d = normalize.normalize_row(parsers.parse("geojson", OSM)[0], ctx).data
        self.assertEqual((d["dostep"], d["w_budynku"], d["pietro"]), ("ograniczony", True, 1))
        self.assertEqual(d["zrodlo_url"], "https://www.openstreetmap.org/node/42")

    def test_point_outside_poland_invalid(self):
        result = normalize.normalize_row(parsers.RawRow("1", {"nazwa": "X", "lat": "48.1", "lon": "11.5"}), CTX)
        self.assertFalse(result.valid)
        self.assertIn("wspolrzedne_poza_polska", result.flags)

    def test_coverage_ignores_unknown(self):
        cov = normalize.coverage([{"nazwa": "A", "dostep": "nieznany"}, {"nazwa": "B"}])
        self.assertEqual((cov["fields"]["nazwa"], cov["fields"]["dostep"]), (1.0, 0.0))


if __name__ == "__main__":
    unittest.main()

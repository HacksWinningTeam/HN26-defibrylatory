"""Map raw source rows to the standard AED schema and normalize values (T03).

Rules: never invent data; when a value is fixed (swapped coordinates, 6-digit TERC, street
type spelled out) a quality flag records it; records with unusable coordinates are kept but
marked ``valid=False`` and excluded from the merge.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date

from mcod.aed.parsers import RawRow
from mcod.aed.schema import (
    FIELD_NAMES,
    FIELDS_BY_NAME,
    PL_LAT_MAX,
    PL_LAT_MIN,
    PL_LON_MAX,
    PL_LON_MIN,
)


def norm_key(header: str) -> str:
    """'Szerokość geograficzna ' -> 'szerokosc_geograficzna'; 'addr:city' -> 'addr_city'."""
    text = str(header).replace("ł", "l").replace("Ł", "L")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _strip_pl(value: str) -> str:
    return value.replace("ł", "l").replace("Ł", "L")


# Header synonyms (normalized keys) → standard field. Order = preference.
SYNONYMS: dict[str, tuple[str, ...]] = {
    "szerokosc_geograficzna": ("szerokosc_geograficzna", "szerokosc", "lat", "latitude", "y"),
    "dlugosc_geograficzna": ("dlugosc_geograficzna", "dlugosc", "lon", "lng", "longitude", "x"),
    "nazwa": ("nazwa_obiektu", "location_object_name", "lokalizacja", "nazwa", "name"),
    "opis_lokalizacji": (
        "opis_lokalizacji", "location_description", "defibrillator_location_pl",
        "defibrillator_location",
    ),
    "miejscowosc": ("miejscowosc", "location_city", "city", "addr_city", "miasto"),
    "cecha_ulicy": ("cecha_ulicy",),
    "nazwa_ulicy": ("nazwa_ulicy", "location_street", "street", "addr_street", "ulica"),
    "nr_budynku": ("nr_budynku", "location_building", "home_number", "addr_housenumber"),
    "nr_lokalu": ("nr_lokalu",),
    "kod_pocztowy": ("kod_pocztowy", "location_postcode", "postcode", "addr_postcode"),
    "kod_terc": ("kod_terc",),
    "kod_simc": ("kod_simc",),
    "telefon_kontaktowy": ("telefon_kontaktowy", "telefon", "phone", "emergency_phone"),
    "email_kontaktowy": ("email_kontaktowy", "email"),
    "dysponent": ("dysponent", "operator"),
    "producent": ("producent", "device_manufacturer", "manufacturer"),
    "model": ("model",),
    "godziny_dostepnosci": ("godziny_dostepnosci", "opening_hours"),
    "pietro": ("pietro", "level"),
    "id_aed": ("id_aed", "numer_id", "defibrillator_id", "ref", "id"),
}
ADDRESS_KEYS = ("adres", "address", "addr_full")
GENERIC_NAMES = re.compile(r"^\s*(defibrylator|aed|defibrylator aed)\s*$", re.IGNORECASE)

CECHA_MAP = {
    "ul": "ul.", "ulica": "ul.", "al": "al.", "aleja": "al.", "aleje": "al.", "pl": "pl.",
    "plac": "pl.", "os": "os.", "osiedle": "os.", "rondo": "rondo", "skwer": "skwer",
    "rynek": "rynek", "bulw": "bulw.", "bulwar": "bulw.", "wyb": "wyb.", "wybrzeze": "wyb.",
    "droga": "droga", "park": "park",
}
STREET_RE = re.compile(
    r"^\s*(?:(?P<cecha>ul|ulica|al|aleja|aleje|pl|plac|os|osiedle|rondo|skwer|rynek|bulw|"
    r"bulwar|wyb|droga|park)\.*\s+)?(?P<name>.+?)(?:\s+(?P<nr>\d+[A-Za-z]?(?:[/-]\d+[A-Za-z]?)?))?"
    r"\s*$",
    re.IGNORECASE,
)
POSTCODE_CITY_RE = re.compile(r"(?P<kod>\d{2}-\d{3})\s+(?P<city>[^,]+)")
POSTCODE_RE = re.compile(r"^\d{2}-\d{3}$")

OSM_ACCESS = {
    "yes": "publiczny", "public": "publiczny", "permissive": "publiczny",
    "customers": "ograniczony", "permit": "ograniczony", "delivery": "ograniczony",
    "private": "prywatny", "no": "prywatny",
}


@dataclass
class SourceContext:
    """Metadata of the source used to fill provenance fields."""

    kind: str  # dane_gov_pl | osm
    key: str  # stable source prefix, e.g. "dane_gov_pl:3624"
    name: str  # human name for `zrodlo`
    url: str
    updated: date | None


@dataclass
class Normalized:
    data: dict
    lat: float | None
    lon: float | None
    valid: bool
    flags: list[str] = field(default_factory=list)


def _clean(value) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def _to_float(value) -> float | None:
    text = _clean(value).replace(",", ".")
    try:
        return float(text) if text else None
    except ValueError:
        return None


def _pick(props_n: dict[str, str], standard: str) -> str:
    for key in SYNONYMS.get(standard, ()):
        value = _clean(props_n.get(key))
        if value:
            if standard == "nazwa" and GENERIC_NAMES.match(value):
                continue
            return value
    return ""


def split_street(text: str) -> tuple[str, str, str]:
    """'ul. Stanisława Wyspiańskiego 20' -> ('ul.', 'Stanisława Wyspiańskiego', '20')."""
    match = STREET_RE.match(_clean(text))
    if not match:
        return "", _clean(text), ""
    cecha_raw = (match.group("cecha") or "").lower()
    cecha = CECHA_MAP.get(_strip_pl(cecha_raw), "")
    return cecha, _clean(match.group("name")).strip(" ,"), match.group("nr") or ""


def parse_address(text: str) -> dict[str, str]:
    """Split 'ul. Jasna 5, 38-400 Krosno' into TERYT-style address fields."""
    result: dict[str, str] = {}
    text = _clean(text)
    if not text:
        return result
    postcode = POSTCODE_CITY_RE.search(text)
    street_part = text
    if postcode:
        result["kod_pocztowy"] = postcode.group("kod")
        result["miejscowosc"] = _clean(postcode.group("city"))
        street_part = text[: postcode.start()].strip(" ,")
    if street_part:
        cecha, name, nr = split_street(street_part)
        if cecha:
            result["cecha_ulicy"] = cecha
        if name:
            result["nazwa_ulicy"] = name
        if nr:
            result["nr_budynku"] = nr
    return result


def _bool_pl(value: str) -> bool | None:
    v = norm_key(value)
    if v in ("tak", "yes", "true", "1", "wewnatrz_budynku", "wewnatrz"):
        return True
    if v in ("nie", "no", "false", "0", "na_zewnatrz", "na_zewnatrz_budynku", "zewnatrz"):
        return False
    return None


def _apply_osm(props: dict, data: dict, flags: list[str]) -> None:
    access = _clean(props.get("access")).lower()
    data["dostep"] = OSM_ACCESS.get(access, "nieznany")
    indoor = _bool_pl(_clean(props.get("indoor")))
    if indoor is not None:
        data["w_budynku"] = indoor
    if props.get("description"):
        data["instrukcja_dojscia"] = _clean(props.get("description"))
    check = _clean(props.get("check_date"))
    if re.match(r"^\d{4}-\d{2}-\d{2}$", check):
        data["data_aktualizacji"] = check
    if props.get("@osm_id") is not None:
        osm_type = props.get("@osm_type", "node")
        data["zrodlo_url"] = f"https://www.openstreetmap.org/{osm_type}/{props['@osm_id']}"


def _apply_warsaw(props_n: dict, data: dict, flags: list[str]) -> None:
    public = norm_key(_clean(props_n.get("device_public_access")))
    data["dostep"] = {"publiczny": "publiczny", "prywatny": "prywatny"}.get(public, "nieznany")
    availability = _clean(props_n.get("device_availability"))
    hours_text = _clean(props_n.get("device_access_description"))
    if norm_key(availability) == "tak":
        data["godziny_dostepnosci"] = "24/7"
    elif hours_text:
        data["godziny_dostepnosci"] = hours_text
        flags.append("godziny_tekstem")  # free text, not opening_hours syntax
    location = _bool_pl(_clean(props_n.get("device_location")))
    if location is not None:
        data["w_budynku"] = location


def _coerce(field_name: str, value):
    spec = FIELDS_BY_NAME[field_name]
    if spec.type == "integer":
        try:
            return int(float(str(value).replace(",", ".")))
        except (TypeError, ValueError):
            return None
    return value


def normalize_row(row: RawRow, ctx: SourceContext) -> Normalized:
    props = row.props or {}
    props_n = {norm_key(k): v for k, v in props.items()}
    flags: list[str] = []
    data: dict = {}

    for standard in SYNONYMS:
        if standard in ("szerokosc_geograficzna", "dlugosc_geograficzna"):
            continue
        value = _pick(props_n, standard)
        if value:
            data[standard] = value

    # Full address string (Krosno, Marki) → TERYT-style parts, without overwriting.
    for key in ADDRESS_KEYS:
        if props_n.get(key):
            for k, v in parse_address(props_n[key]).items():
                data.setdefault(k, v)
            break
    # "ul. Rakowiecka" given as street → split type and number.
    if data.get("nazwa_ulicy") and not data.get("cecha_ulicy"):
        cecha, name, nr = split_street(data["nazwa_ulicy"])
        if cecha:
            data["cecha_ulicy"], data["nazwa_ulicy"] = cecha, name
            if nr and not data.get("nr_budynku"):
                data["nr_budynku"] = nr
    if data.get("cecha_ulicy"):
        raw_cecha = data["cecha_ulicy"]
        cecha = CECHA_MAP.get(_strip_pl(raw_cecha.lower().rstrip(".")))
        if cecha:
            if cecha != raw_cecha:
                flags.append("cecha_ulicy_znormalizowana")
            data["cecha_ulicy"] = cecha
        else:
            data["cecha_ulicy"] = "inne"
    if data.get("kod_pocztowy") and not POSTCODE_RE.match(data["kod_pocztowy"]):
        flags.append("kod_pocztowy_niepoprawny")
        data.pop("kod_pocztowy")
    for code in ("kod_terc", "kod_simc"):
        if data.get(code):
            digits = re.sub(r"\D", "", data[code])
            if len(digits) == 7:
                data[code] = digits
            else:
                flags.append(f"{code}_niepoprawny")
                data.pop(code)

    if ctx.kind == "osm":
        _apply_osm(props, data, flags)
    if "device_public_access" in props_n:
        _apply_warsaw(props_n, data, flags)

    # Coordinates: geometry first, then tabular columns.
    lon, lat = row.lon, row.lat
    if lat is None or lon is None:
        lat = _to_float(_pick(props_n, "szerokosc_geograficzna"))
        lon = _to_float(_pick(props_n, "dlugosc_geograficzna"))
    valid = lat is not None and lon is not None
    if valid:
        in_pl = PL_LAT_MIN <= lat <= PL_LAT_MAX and PL_LON_MIN <= lon <= PL_LON_MAX
        swapped = PL_LAT_MIN <= lon <= PL_LAT_MAX and PL_LON_MIN <= lat <= PL_LON_MAX
        if not in_pl and swapped:
            lat, lon = lon, lat
            flags.append("wspolrzedne_zamienione")
        elif not in_pl:
            flags.append("wspolrzedne_poza_polska")
            valid = False
    else:
        flags.append("brak_wspolrzednych")
    if valid:
        data["szerokosc_geograficzna"] = round(lat, 6)
        data["dlugosc_geograficzna"] = round(lon, 6)

    if not data.get("nazwa"):
        fallback = data.get("dysponent") or data.get("opis_lokalizacji")
        data["nazwa"] = f"AED – {fallback}"[:255] if fallback else "AED"
        flags.append("nazwa_uzupelniona")
    if not data.get("miejscowosc"):
        flags.append("brak_miejscowosci")
    data.setdefault("dostep", "nieznany")
    if data.get("pietro") is not None:
        data["pietro"] = _coerce("pietro", data["pietro"])
        if data["pietro"] is None:
            data.pop("pietro")

    source_id = data.get("id_aed") or row.row_id
    data["id_aed"] = re.sub(r"[^A-Za-z0-9._-]", "-", f"{ctx.key}-{source_id}")[:64]
    data["zrodlo"] = ctx.name
    data.setdefault("zrodlo_url", ctx.url)
    if "data_aktualizacji" not in data and ctx.updated:
        data["data_aktualizacji"] = ctx.updated.isoformat()

    data = {k: data[k] for k in FIELD_NAMES if k in data and data[k] not in ("", None)}
    lat_out = data.get("szerokosc_geograficzna")
    lon_out = data.get("dlugosc_geograficzna")
    return Normalized(data=data, lat=lat_out, lon=lon_out, valid=valid, flags=flags)


def coverage(records: list[dict]) -> dict:
    """Share of records with a non-empty value, per standard field (+ group summaries)."""
    total = len(records)
    empty = (None, "", "nieznany")  # "unknown" is not information
    fields = {
        name: (round(sum(1 for r in records if r.get(name) not in empty) / total, 3)
               if total else 0.0)
        for name in FIELD_NAMES
    }

    def avg(names: list[str]) -> float:
        return round(sum(fields[n] for n in names) / len(names), 3) if names else 0.0

    required = [n for n in FIELD_NAMES if FIELDS_BY_NAME[n].obligation == "wymagane"]
    recommended = [n for n in FIELD_NAMES if FIELDS_BY_NAME[n].obligation == "zalecane"]
    return {
        "records": total,
        "required": avg(required),
        "recommended": avg(recommended),
        "overall": avg(list(FIELD_NAMES)),
        "fields": fields,
    }

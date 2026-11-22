"""Validate data against the AED standard (T14, DEC-014/015).

Two separate answers:
  * ``valid``    — full conformance: every required field present as a column named like the
                   standard and no row errors (what a data owner should aim for).
  * ``blocking`` — whether the portal refuses to publish it: unreadable, no rows, no usable
                   coordinates at all, or invalid rows above the standard's ``max_invalid_ratio``.

Row errors: missing / invalid coordinates (or outside Poland), an empty required value in a
standard-named column, wrong type / allowed value / pattern / range / length.
Warnings: required fields the portal derives from the dataset metadata (id_aed, zrodlo,
data_aktualizacji, dostep), missing town, columns recognised under a non-standard name.
"""
import io
import re
import uuid
import zipfile
from collections import Counter, OrderedDict
from datetime import date

from mcod.aed import normalize, parsers
from mcod.aed.schema import FIELD_NAMES, FIELDS_BY_NAME, SCHEMA_VERSION

MAX_ERRORS = 500
MAX_EXAMPLES = 5
DEFAULT_MAX_INVALID_RATIO = 0.2
COORD_FIELDS = ("szerokosc_geograficzna", "dlugosc_geograficzna")
REQUIRED = [name for name in FIELD_NAMES if FIELDS_BY_NAME[name].required]
# Required fields the portal can fill from the dataset/resource metadata when a column is absent.
DERIVABLE = {
    "id_aed": "numer wiersza",
    "zrodlo": "nazwa instytucji / zbioru",
    "data_aktualizacji": "data danych zasobu",
    "dostep": "„nieznany”",
}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TRUE_VALUES = {"true", "tak", "1", "yes"}
FALSE_VALUES = {"false", "nie", "0", "no"}

MESSAGES = {
    "required": "Brak wartości wymaganego pola „{field}”.",
    "type_number": "Wartość „{value}” pola „{field}” nie jest liczbą.",
    "type_integer": "Wartość „{value}” pola „{field}” nie jest liczbą całkowitą.",
    "type_boolean": "Wartość „{value}” pola „{field}” nie jest wartością logiczną (true/false).",
    "type_date": "Wartość „{value}” pola „{field}” nie jest datą w formacie RRRR-MM-DD.",
    "allowed_values": "Wartość „{value}” pola „{field}” spoza listy dozwolonych wartości.",
    "pattern": "Wartość „{value}” pola „{field}” ma niepoprawny format.",
    "minimum": "Wartość {value} pola „{field}” jest mniejsza od minimum.",
    "maximum": "Wartość {value} pola „{field}” jest większa od maksimum.",
    "max_length": "Wartość pola „{field}” jest za długa.",
    "coordinates_missing": "Brak współrzędnych geograficznych.",
    "coordinates_outside_poland": "Współrzędne ({value}) leżą poza Polską.",
    "duplicate_id": "Identyfikator „{value}” występuje w zbiorze więcej niż raz.",
}
WARNING_MESSAGES = {
    "required_derived": "Brak wymaganej kolumny „{field}” – portal uzupełni ją z metadanych ({value}).",
    "column_synonym": "Kolumna „{value}” rozpoznana jako „{field}” – użyj nazwy ze standardu.",
    "column_address": "Kolumna „{value}” (pełny adres) rozbita na pola adresowe standardu.",
    "column_unknown": "Kolumna „{value}” nie należy do standardu i zostanie pominięta.",
    "coordinates_swapped": "Zamienione współrzędne (szerokość/długość) – poprawione automatycznie.",
    "town_missing": "Brak miejscowości – pole wymagane, uzupełnij dane.",
    "recommended_missing": "Brak zalecanej kolumny „{field}”.",
}


class ValidationInputError(ValueError):
    """Input cannot be read at all (400)."""


def detect_format(raw, filename=None, hint=None):
    """csv | xlsx | json | geojson | xml from an explicit hint, the file name or the content."""
    if hint:
        hint = hint.lower().lstrip(".")
        return "json" if hint == "jsonapi" else hint
    if filename:
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext in ("csv", "tsv", "txt"):
            return "csv"
        if ext in ("xlsx", "xls"):
            return "xlsx"
        if ext in ("geojson",):
            return "geojson"
        if ext in ("json", "xml"):
            return ext
    head = raw[:4096].lstrip()
    if raw[:2] == b"PK":
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                if any(name.startswith("xl/") for name in zf.namelist()):
                    return "xlsx"
        except zipfile.BadZipFile:
            pass
    if head[:1] in (b"{", b"["):
        return "geojson" if b"FeatureCollection" in raw[:20000] else "json"
    if head[:1] == b"<":
        return "xml"
    return "csv"


def _message(code, field="", value="", warning=False):
    template = (WARNING_MESSAGES if warning else MESSAGES).get(code, code)
    return template.format(field=field, value=value)


def map_columns(columns, has_geometry=False, strict=False):
    """source column -> {"field": standard field or None, "match": exact|synonym|address|geometry|unknown}."""
    synonym_of = {}
    for standard, keys in normalize.SYNONYMS.items():
        for key in keys:
            synonym_of.setdefault(key, standard)
    mapping = OrderedDict()
    for column in columns:
        key = normalize.norm_key(column)
        if key in FIELDS_BY_NAME:
            mapping[column] = {"field": key, "match": "exact"}
        elif not strict and key in synonym_of:
            mapping[column] = {"field": synonym_of[key], "match": "synonym"}
        elif not strict and key in normalize.ADDRESS_KEYS:
            mapping[column] = {"field": "adres", "match": "address"}
        else:
            mapping[column] = {"field": None, "match": "unknown"}
    if has_geometry:
        mapping["(geometria)"] = {"field": "szerokosc_geograficzna, dlugosc_geograficzna", "match": "geometry"}
    return mapping


def _covered_fields(mapping):
    covered, exact = set(), set()
    for info in mapping.values():
        field = info["field"]
        if not field:
            continue
        if info["match"] == "geometry":
            covered.update(COORD_FIELDS)
        elif info["match"] == "address":
            covered.update(("miejscowosc", "nazwa_ulicy", "nr_budynku", "kod_pocztowy"))
        else:
            covered.add(field)
            if info["match"] == "exact":
                exact.add(field)
    return covered, exact


def _check_value(spec, value):
    """Error code for a non-empty raw value of a standard-named column, or None."""
    text = str(value).strip()
    if spec.type == "number":
        try:
            number = float(text.replace(",", "."))
        except ValueError:
            return "type_number"
        if spec.minimum is not None and number < spec.minimum:
            return "minimum"
        if spec.maximum is not None and number > spec.maximum:
            return "maximum"
        return None
    if spec.type == "integer":
        try:
            number = float(text.replace(",", "."))
        except ValueError:
            return "type_integer"
        if number != int(number):
            return "type_integer"
        if spec.minimum is not None and number < spec.minimum:
            return "minimum"
        if spec.maximum is not None and number > spec.maximum:
            return "maximum"
        return None
    if spec.type == "boolean":
        return None if text.lower() in TRUE_VALUES | FALSE_VALUES else "type_boolean"
    if spec.type == "date":
        if not DATE_RE.match(text):
            return "type_date"
        try:
            date.fromisoformat(text)
        except ValueError:
            return "type_date"
        return None
    if spec.allowed_values and text not in spec.allowed_codes:
        return "allowed_values"
    if spec.pattern and not re.match(spec.pattern, text):
        return "pattern"
    if spec.max_length and len(text) > spec.max_length:
        return "max_length"
    return None


def validate_rows(rows, strict=False, max_invalid_ratio=DEFAULT_MAX_INVALID_RATIO, fmt=None):
    """Validate parsed rows (`parsers.RawRow`) -> report dict (attributes of `aed_validation`)."""
    columns = []
    seen = set()
    for row in rows[:2000]:
        for key in (row.props or {}).keys():
            if key not in seen:
                seen.add(key)
                columns.append(key)
    has_geometry = any(row.lat is not None and row.lon is not None for row in rows[:2000])
    mapping = map_columns(columns, has_geometry=has_geometry, strict=strict)
    covered, exact = _covered_fields(mapping)
    exact_columns = {info["field"]: column for column, info in mapping.items() if info["match"] == "exact"}

    errors = []
    error_count = 0
    warnings = Counter()
    warning_examples = {}
    invalid_rows = set()

    def add_error(row_no, field, code, value=""):
        nonlocal error_count
        error_count += 1
        invalid_rows.add(row_no)
        if len(errors) < MAX_ERRORS:
            errors.append({
                "row": row_no, "field": field, "code": code,
                "message": _message(code, field, value), "value": "" if value is None else str(value)[:200],
            })

    def add_warning(code, field="", value="", row_no=None):
        key = (code, field)
        warnings[key] += 1
        warning_examples.setdefault(key, {"field": field, "value": value, "rows": []})
        if row_no is not None and len(warning_examples[key]["rows"]) < MAX_EXAMPLES:
            warning_examples[key]["rows"].append(row_no)

    # Column-level findings.
    missing_required = []
    for field in REQUIRED:
        if field in exact or (field in covered and not strict):
            continue
        if field in DERIVABLE and not strict:
            add_warning("required_derived", field, DERIVABLE[field])
            continue
        if field == "miejscowosc" and not strict:
            continue  # reported per row as a warning (town_missing)
        missing_required.append(field)
    for column, info in mapping.items():
        if info["match"] == "synonym":
            add_warning("column_synonym", info["field"], column)
        elif info["match"] == "address":
            add_warning("column_address", "adres", column)
        elif info["match"] == "unknown":
            add_warning("column_unknown", "", column)
    for name in FIELD_NAMES:
        if FIELDS_BY_NAME[name].obligation == "zalecane" and name not in covered:
            add_warning("recommended_missing", name)

    ctx = normalize.SourceContext(kind="validation", key="row", name="", url="", updated=None)
    normalized = []
    ids = Counter()
    coordinates_usable = 0
    for index, row in enumerate(rows, start=1):
        props = row.props or {}
        # Typed checks of standard-named columns.
        for field, column in exact_columns.items():
            if field in COORD_FIELDS:
                continue
            value = props.get(column)
            empty = value is None or str(value).strip() == ""
            spec = FIELDS_BY_NAME[field]
            if empty:
                # missing town is a warning (OSM has none for most points), derivable fields are filled
                if spec.required and field not in DERIVABLE and field != "miejscowosc":
                    add_error(index, field, "required")
                continue
            code = _check_value(spec, value)
            if code:
                add_error(index, field, code, value)
        # Coordinates + normalisation (also handles synonyms, geometry, swapped lat/lon).
        result = normalize.normalize_row(row, ctx)
        if "brak_wspolrzednych" in result.flags:
            add_error(index, "szerokosc_geograficzna", "coordinates_missing")
        elif "wspolrzedne_poza_polska" in result.flags:
            lat, lon = row.lat, row.lon
            if lat is None:
                lat = props.get(exact_columns.get("szerokosc_geograficzna", ""), "")
                lon = props.get(exact_columns.get("dlugosc_geograficzna", ""), "")
            add_error(index, "szerokosc_geograficzna", "coordinates_outside_poland", "{}, {}".format(lat, lon))
        else:
            coordinates_usable += 1
            if "wspolrzedne_zamienione" in result.flags:
                add_warning("coordinates_swapped", "szerokosc_geograficzna", row_no=index)
        if not result.data.get("miejscowosc"):
            add_warning("town_missing", "miejscowosc", row_no=index)
        if "id_aed" in exact_columns:
            raw_id = str(props.get(exact_columns["id_aed"]) or "").strip()
            if raw_id:
                ids[raw_id] += 1
                if ids[raw_id] == 2:
                    add_error(index, "id_aed", "duplicate_id", raw_id)
        normalized.append(result.data)

    rows_total = len(rows)
    rows_invalid = len(invalid_rows)
    invalid_ratio = (rows_invalid / rows_total) if rows_total else 1.0
    blocking_reasons = []
    if rows_total == 0:
        blocking_reasons.append("Plik nie zawiera żadnych wierszy danych.")
    elif coordinates_usable == 0:
        blocking_reasons.append("Żaden wiersz nie ma poprawnych współrzędnych geograficznych w Polsce.")
    if rows_total and invalid_ratio > max_invalid_ratio:
        blocking_reasons.append(
            "Błędne wiersze: {:.0%} (dopuszczalne: {:.0%}).".format(invalid_ratio, max_invalid_ratio)
        )
    if strict and missing_required:
        blocking_reasons.append("Brak wymaganych kolumn: {}.".format(", ".join(missing_required)))

    valid = rows_total > 0 and rows_invalid == 0 and not missing_required and all(
        field in exact for field in REQUIRED
    )
    # valid = full conformance (only "recommended" warnings allowed); warnings = publishable but not
    # fully conformant; invalid = blocking.
    if blocking_reasons:
        status = "invalid"
    elif valid:
        status = "valid"
    else:
        status = "warnings"

    cov = normalize.coverage(normalized) if normalized else normalize.coverage([])
    warning_list = []
    for (code, field), count in warnings.most_common():
        example = warning_examples[(code, field)]
        warning_list.append({
            "code": code, "field": field or None, "count": count,
            "message": _message(code, field, example["value"], warning=True),
            "rows": example["rows"],
        })
    return {
        "standard": "aed-pl",
        "schema_version": SCHEMA_VERSION,
        "format": fmt,
        "strict": strict,
        "valid": valid,
        "status": status,
        "blocking": bool(blocking_reasons),
        "blocking_reasons": blocking_reasons,
        "rows_total": rows_total,
        "rows_valid": rows_total - rows_invalid,
        "rows_invalid": rows_invalid,
        "invalid_ratio": round(invalid_ratio, 4) if rows_total else None,
        "max_invalid_ratio": max_invalid_ratio,
        "column_mapping": {column: info for column, info in mapping.items()},
        "unknown_columns": [c for c, i in mapping.items() if i["match"] == "unknown"],
        "missing_required_fields": missing_required,
        "coverage": cov,
        "errors_count": error_count,
        "errors": errors,
        "errors_truncated": error_count > len(errors),
        "warnings": warning_list,
    }


def validate_bytes(raw, filename=None, fmt=None, strict=False, max_invalid_ratio=DEFAULT_MAX_INVALID_RATIO):
    """Parse + validate raw file content. Raises ValidationInputError for unreadable input."""
    if not raw:
        raise ValidationInputError("Pusty plik / brak danych.")
    fmt = detect_format(raw, filename=filename, hint=fmt)
    try:
        rows = parsers.parse(fmt, raw)
    except parsers.ParseError as exc:
        raise ValidationInputError("Nie można odczytać danych jako {}: {}".format(fmt, exc))
    except Exception as exc:  # malformed files raise all kinds of errors in csv/openpyxl/json
        raise ValidationInputError("Nie można odczytać danych jako {}: {}".format(fmt, exc))
    return validate_rows(rows, strict=strict, max_invalid_ratio=max_invalid_ratio, fmt=fmt)


def new_report_id():
    return str(uuid.uuid4())


def unreadable_report(message, fmt=None, max_invalid_ratio=DEFAULT_MAX_INVALID_RATIO):
    """Report stored for resources whose data cannot be read (blocking)."""
    return {
        "standard": "aed-pl", "schema_version": SCHEMA_VERSION, "format": fmt, "strict": False,
        "valid": False, "status": "error", "blocking": True, "blocking_reasons": [message],
        "rows_total": 0, "rows_valid": 0, "rows_invalid": 0, "invalid_ratio": None,
        "max_invalid_ratio": max_invalid_ratio, "column_mapping": {}, "unknown_columns": [],
        "missing_required_fields": [], "coverage": {}, "errors_count": 0, "errors": [],
        "errors_truncated": False, "warnings": [],
    }


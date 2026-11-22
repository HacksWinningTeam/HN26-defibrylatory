"""Generic engine for data-defined standards (T17 validation, T18 conversion/merge; DEC-019).

Same report shape as the AED validator (`validation.validate_rows`), so stored results, admin messages,
blocking and the API work unchanged. Rules come only from the standard's definition (`StandardSpec`):
column mapping by field name or declared synonym, type / required / allowed values / pattern / range /
length per field, duplicate identifiers, blocking threshold.
"""
import re
from collections import Counter, OrderedDict
from datetime import date

from mcod.aed import normalize

MAX_ERRORS = 500
MAX_EXAMPLES = 5
TRUE_VALUES = {"true", "tak", "1", "yes", "t", "x"}
FALSE_VALUES = {"false", "nie", "0", "no", "f"}
DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})(?:[ T].*)?$")
DATE_PL_RE = re.compile(r"^(\d{1,2})[./](\d{1,2})[./](\d{4})$")

MESSAGES = {
    "required": "Brak wartości wymaganego pola „{field}”.",
    "type_number": "Wartość „{value}” pola „{field}” nie jest liczbą.",
    "type_integer": "Wartość „{value}” pola „{field}” nie jest liczbą całkowitą.",
    "type_boolean": "Wartość „{value}” pola „{field}” nie jest wartością logiczną (tak/nie).",
    "type_date": "Wartość „{value}” pola „{field}” nie jest datą w formacie RRRR-MM-DD.",
    "allowed_values": "Wartość „{value}” pola „{field}” spoza listy dozwolonych wartości.",
    "pattern": "Wartość „{value}” pola „{field}” ma niepoprawny format.",
    "minimum": "Wartość {value} pola „{field}” jest mniejsza od minimum.",
    "maximum": "Wartość {value} pola „{field}” jest większa od maksimum.",
    "max_length": "Wartość pola „{field}” jest za długa.",
    "duplicate_id": "Identyfikator „{value}” występuje w zbiorze więcej niż raz.",
}
WARNING_MESSAGES = {
    "required_derived": "Brak wymaganej kolumny „{field}” – portal uzupełni ją z metadanych ({value}).",
    "column_synonym": "Kolumna „{value}” rozpoznana jako „{field}” – użyj nazwy ze standardu.",
    "column_unknown": "Kolumna „{value}” nie należy do standardu i zostanie pominięta.",
    "recommended_missing": "Brak zalecanej kolumny „{field}”.",
    "value_converted": "Wartości pola „{field}” zapisane niezgodnie ze standardem (np. „{value}”) – przekształcone automatycznie.",
}


def _message(code, field="", value="", warning=False):
    return (WARNING_MESSAGES if warning else MESSAGES).get(code, code).format(field=field, value=value)


def map_columns(columns, spec, has_geometry=False, strict=False):
    """source column -> {"field": standard field or None, "match": exact|synonym|geometry|unknown}."""
    synonyms = spec.synonym_map()
    mapping = OrderedDict()
    used = set()
    for column in columns:
        key = normalize.norm_key(column)
        if key in spec.by_name and key not in used:
            mapping[column] = {"field": key, "match": "exact"}
            used.add(key)
        elif not strict and key in synonyms and synonyms[key] not in used:
            mapping[column] = {"field": synonyms[key], "match": "synonym"}
            used.add(synonyms[key])
        else:
            mapping[column] = {"field": None, "match": "unknown"}
    geo = spec.geo_fields
    if has_geometry and geo and not (set(geo) & used):
        mapping["(geometria)"] = {"field": ", ".join(geo), "match": "geometry"}
        used.update(geo)
    return mapping


def _clean(value):
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def coerce(field, raw):
    """-> (value, error_code, converted). Empty -> (None, None, False)."""
    text = _clean(raw)
    if text == "":
        return None, None, False
    ftype = field.get("type", "string")
    converted = False
    if ftype in ("number", "integer"):
        candidate = text.replace(" ", "").replace(",", ".")
        try:
            number = float(candidate)
        except ValueError:
            return None, "type_number" if ftype == "number" else "type_integer", False
        converted = candidate != text
        if ftype == "integer":
            if number != int(number):
                return None, "type_integer", False
            number = int(number)
        if field.get("minimum") is not None and number < field["minimum"]:
            return None, "minimum", False
        if field.get("maximum") is not None and number > field["maximum"]:
            return None, "maximum", False
        return number, None, converted
    if ftype == "boolean":
        lowered = text.lower()
        if lowered in TRUE_VALUES:
            return True, None, lowered not in ("true",)
        if lowered in FALSE_VALUES:
            return False, None, lowered not in ("false",)
        return None, "type_boolean", False
    if ftype == "date":
        match = DATE_RE.match(text)
        if match:
            try:
                value = date(int(match.group(1)), int(match.group(2)), int(match.group(3))).isoformat()
            except ValueError:
                return None, "type_date", False
            return value, None, value != text
        match = DATE_PL_RE.match(text)
        if match:
            try:
                return date(int(match.group(3)), int(match.group(2)), int(match.group(1))).isoformat(), None, True
            except ValueError:
                return None, "type_date", False
        return None, "type_date", False
    # string
    if field.get("allowed_values"):
        codes = [v["value"] for v in field["allowed_values"]]
        if text not in codes:
            lowered = normalize.norm_key(text)
            match = next((c for c in codes if normalize.norm_key(c) == lowered or
                          normalize.norm_key(next((v["label"] for v in field["allowed_values"] if v["value"] == c), "")) == lowered), None)
            if match is None:
                return None, "allowed_values", False
            return match, None, True
    if field.get("pattern") and not re.match(field["pattern"], text):
        compact = re.sub(r"[\s-]", "", text) if field.get("name") in ("regon", "nip") else text
        if compact != text and re.match(field["pattern"], compact):
            return compact, None, True
        return None, "pattern", False
    if field.get("max_length") and len(text) > field["max_length"]:
        return None, "max_length", False
    return text, None, False


def convert_row(row, mapping, spec):
    """RawRow -> (data dict keyed by standard fields, [(field, code, raw)], {converted fields})."""
    props = row.props or {}
    data, errors, converted = {}, [], set()
    for column, info in mapping.items():
        field_name = info["field"]
        if not field_name or info["match"] == "geometry":
            continue
        field = spec.by_name[field_name]
        value, code, was_converted = coerce(field, props.get(column))
        if code:
            errors.append((field_name, code, props.get(column)))
        elif value is not None:
            data[field_name] = value
            if was_converted:
                converted.add((field_name, _clean(props.get(column))))
    geo = spec.geo_fields
    if geo and "(geometria)" in mapping and row.lat is not None and row.lon is not None:
        for field_name, raw in zip(geo, (row.lat, row.lon)):
            value, code, _ = coerce(spec.by_name[field_name], raw)
            if code:
                errors.append((field_name, code, raw))
            elif value is not None:
                data[field_name] = value
    return data, errors, converted


def coverage(records, spec):
    total = len(records)
    fields = {
        name: (round(sum(1 for r in records if r.get(name) not in (None, "")) / total, 3) if total else 0.0)
        for name in spec.names
    }

    def avg(names):
        return round(sum(fields[n] for n in names) / len(names), 3) if names else 0.0

    return {"records": total, "required": avg(spec.required), "recommended": avg(spec.recommended),
            "overall": avg(spec.names), "fields": fields}


def id_field(spec):
    return next((f["name"] for f in spec.fields if f["name"].startswith("id")), None)


def validate_rows(rows, spec, strict=False, max_invalid_ratio=0.2, fmt=None, collect_invalid=False):
    columns, seen = [], set()
    for row in rows[:2000]:
        for key in (row.props or {}).keys():
            if key not in seen:
                seen.add(key)
                columns.append(key)
    has_geometry = any(row.lat is not None and row.lon is not None for row in rows[:2000])
    mapping = map_columns(columns, spec, has_geometry=has_geometry, strict=strict)
    mapped = {}
    for column, info in mapping.items():
        if info["match"] == "geometry":
            for name in info["field"].split(", "):
                mapped[name] = "geometry"
        elif info["field"]:
            mapped[info["field"]] = info["match"]

    errors, error_count, invalid_rows = [], 0, set()
    warnings, warning_examples = Counter(), {}

    def add_error(row_no, field, code, value=""):
        nonlocal error_count
        error_count += 1
        invalid_rows.add(row_no)
        if len(errors) < MAX_ERRORS:
            errors.append({"row": row_no, "field": field, "code": code, "message": _message(code, field, value),
                           "value": "" if value is None else str(value)[:200]})

    def add_warning(code, field="", value="", row_no=None):
        key = (code, field)
        warnings[key] += 1
        warning_examples.setdefault(key, {"value": value, "rows": []})
        if row_no is not None and len(warning_examples[key]["rows"]) < MAX_EXAMPLES:
            warning_examples[key]["rows"].append(row_no)

    missing_required = []
    derivable = spec.derivable
    for name in spec.required:
        if name in mapped and (mapped[name] == "exact" or not strict):
            continue
        if name in derivable and not strict:
            add_warning("required_derived", name, derivable[name])
        else:
            missing_required.append(name)
    for column, info in mapping.items():
        if info["match"] == "synonym":
            add_warning("column_synonym", info["field"], column)
        elif info["match"] == "unknown":
            add_warning("column_unknown", "", column)
    for name in spec.recommended:
        if name not in mapped:
            add_warning("recommended_missing", name)

    records, ids = [], Counter()
    the_id = id_field(spec)
    for index, row in enumerate(rows, start=1):
        data, row_errors, converted = convert_row(row, mapping, spec)
        for field, code, raw in row_errors:
            add_error(index, field, code, raw)
        for field, raw in converted:
            add_warning("value_converted", field, raw, row_no=index)
        failed = {f for f, _, _ in row_errors}
        for name in spec.required:
            if name in mapped and name not in data and name not in failed and name not in derivable:
                add_error(index, name, "required")
        if the_id and data.get(the_id):
            ids[str(data[the_id])] += 1
            if ids[str(data[the_id])] == 2:
                add_error(index, the_id, "duplicate_id", data[the_id])
        records.append(data)

    rows_total, rows_invalid = len(rows), len(invalid_rows)
    invalid_ratio = (rows_invalid / rows_total) if rows_total else 1.0
    blocking_reasons = []
    if rows_total == 0:
        blocking_reasons.append("Plik nie zawiera żadnych wierszy danych.")
    elif not any(info["field"] for info in mapping.values()):
        blocking_reasons.append("Żadna kolumna pliku nie odpowiada polom standardu.")
    if rows_total and invalid_ratio > max_invalid_ratio:
        blocking_reasons.append("Błędne wiersze: {:.0%} (dopuszczalne: {:.0%}).".format(invalid_ratio, max_invalid_ratio))
    if strict and missing_required:
        blocking_reasons.append("Brak wymaganych kolumn: {}.".format(", ".join(missing_required)))
    valid = rows_total > 0 and rows_invalid == 0 and not missing_required and all(
        mapped.get(name) == "exact" for name in spec.required if name not in derivable)
    status = "invalid" if blocking_reasons else ("valid" if valid else "warnings")
    warning_list = []
    for (code, field), count in warnings.most_common():
        example = warning_examples[(code, field)]
        warning_list.append({"code": code, "field": field or None, "count": count,
                             "message": _message(code, field, example["value"], warning=True), "rows": example["rows"]})
    report = {
        "standard": spec.code, "schema_version": spec.version, "format": fmt, "strict": strict, "valid": valid,
        "status": status, "blocking": bool(blocking_reasons), "blocking_reasons": blocking_reasons,
        "rows_total": rows_total, "rows_valid": rows_total - rows_invalid, "rows_invalid": rows_invalid,
        "invalid_ratio": round(invalid_ratio, 4) if rows_total else None, "max_invalid_ratio": max_invalid_ratio,
        "column_mapping": dict(mapping), "unknown_columns": [c for c, i in mapping.items() if i["match"] == "unknown"],
        "missing_required_fields": missing_required, "coverage": coverage(records, spec),
        "errors_count": error_count, "errors": errors, "errors_truncated": error_count > len(errors),
        "warnings": warning_list,
    }
    if collect_invalid:
        report["_invalid_rows"] = invalid_rows
        report["_records"] = records
        report["_mapping"] = mapping
    return report


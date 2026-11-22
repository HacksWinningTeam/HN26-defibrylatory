"""Data-defined standards (T16, DEC-019).

A standard is described by data (`DataStandard.fields/merge/discovery/publish`, loaded from
`standards/*.json`). `StandardSpec` wraps that definition and generates the same artefacts the AED
standard has in code: field lookup, synonyms, JSON Schema, Table Schema, CSV template and XLSX.

Field definition keys: name, label, type (string|number|integer|boolean|date), obligation
(wymagane|zalecane|opcjonalne), description, example, allowed_values [{value, label}], pattern,
minimum, maximum, max_length, synonyms [header names], derivable (text: what the portal fills in when
the column is missing, e.g. "numer wiersza").
"""
import csv
import io

TYPES = ("string", "number", "integer", "boolean", "date")
OBLIGATIONS = ("wymagane", "zalecane", "opcjonalne")
TYPE_LABELS_PL = {"string": "tekst", "number": "liczba", "integer": "liczba całkowita",
                  "boolean": "tak/nie", "date": "data (RRRR-MM-DD)"}


class StandardDefinitionError(ValueError):
    pass


def norm_key(header):
    from mcod.aed.normalize import norm_key as _norm

    return _norm(header)


class StandardSpec:
    def __init__(self, code, name, version, description, fields, merge=None, discovery=None, publish=None):
        self.code = code
        self.name = name
        self.version = version
        self.description = description or ""
        self.fields = [dict(f) for f in fields]
        self.merge = dict(merge or {"strategy": "none"})
        self.discovery = dict(discovery or {})
        self.publish = dict(publish or {})
        self.validate_definition()
        self.by_name = {f["name"]: f for f in self.fields}
        self.names = [f["name"] for f in self.fields]

    # --- construction --------------------------------------------------------------------------

    @classmethod
    def from_dict(cls, data):
        try:
            return cls(
                code=data["code"], name=data["name"], version=str(data.get("version", "1.0.0")),
                description=data.get("description", ""), fields=data["fields"], merge=data.get("merge"),
                discovery=data.get("discovery"), publish=data.get("publish"),
            )
        except KeyError as exc:
            raise StandardDefinitionError("Brak klucza w definicji standardu: {}".format(exc))

    @classmethod
    def from_model(cls, standard):
        if not standard.fields:
            if standard.code == "aed-pl":
                return cls.from_dict(aed_definition())
            raise StandardDefinitionError("Standard {} nie ma zdefiniowanych pól.".format(standard.code))
        return cls(standard.code, standard.name, standard.version, standard.description, standard.fields,
                   standard.merge, standard.discovery, standard.publish)

    def validate_definition(self):
        if not self.fields:
            raise StandardDefinitionError("Standard musi mieć co najmniej jedno pole.")
        seen = set()
        for f in self.fields:
            name = f.get("name")
            if not name or norm_key(name) != name:
                raise StandardDefinitionError("Nazwa pola musi być w formacie snake_case ASCII: {!r}".format(name))
            if name in seen:
                raise StandardDefinitionError("Powtórzona nazwa pola: {}".format(name))
            seen.add(name)
            f.setdefault("type", "string")
            f.setdefault("obligation", "opcjonalne")
            f.setdefault("label", name)
            f.setdefault("synonyms", [])
            if f["type"] not in TYPES:
                raise StandardDefinitionError("Nieznany typ pola {}: {}".format(name, f["type"]))
            if f["obligation"] not in OBLIGATIONS:
                raise StandardDefinitionError("Nieznana wymagalność pola {}: {}".format(name, f["obligation"]))
        if self.merge.get("strategy") not in ("key", "geo", "none"):
            raise StandardDefinitionError("merge.strategy musi być key, geo albo none")

    def to_dict(self):
        return {"code": self.code, "name": self.name, "version": self.version, "description": self.description,
                "fields": self.fields, "merge": self.merge, "discovery": self.discovery, "publish": self.publish}

    # --- lookups ------------------------------------------------------------------------------

    @property
    def required(self):
        return [f["name"] for f in self.fields if f["obligation"] == "wymagane"]

    @property
    def recommended(self):
        return [f["name"] for f in self.fields if f["obligation"] == "zalecane"]

    @property
    def derivable(self):
        return {f["name"]: f["derivable"] for f in self.fields if f.get("derivable")}

    def synonym_map(self):
        """normalised header -> field name (exact field names first, then declared synonyms)."""
        mapping = {}
        for f in self.fields:
            mapping.setdefault(f["name"], f["name"])
        for f in self.fields:
            for synonym in f.get("synonyms", []):
                mapping.setdefault(norm_key(synonym), f["name"])
        return mapping

    @property
    def geo_fields(self):
        lat, lon = self.publish.get("lat_field"), self.publish.get("lon_field")
        return (lat, lon) if lat in self.by_name and lon in self.by_name else None

    # --- generated artefacts -------------------------------------------------------------------

    def _json_property(self, f):
        prop = {"title": f["label"], "description": f.get("description", "")}
        if f["type"] == "date":
            prop.update({"type": "string", "format": "date"})
        else:
            prop["type"] = f["type"]
        if f.get("allowed_values"):
            prop["enum"] = [v["value"] for v in f["allowed_values"]]
        for key, schema_key in (("pattern", "pattern"), ("minimum", "minimum"), ("maximum", "maximum"),
                                ("max_length", "maxLength")):
            if f.get(key) is not None:
                prop[schema_key] = f[key]
        if f.get("example") not in (None, ""):
            prop["examples"] = [f["example"]]
        if f["obligation"] != "wymagane":
            prop = {"anyOf": [prop, {"type": "null"}, {"const": ""}]}
        return prop

    def json_schema(self):
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "https://dane.gov.pl/schemas/{}/{}/record.schema.json".format(self.code, self.version),
            "title": self.name,
            "description": self.description,
            "type": "object",
            "required": self.required,
            "properties": {f["name"]: self._json_property(f) for f in self.fields},
            "additionalProperties": False,
        }

    def table_schema(self):
        fields = []
        for f in self.fields:
            constraints = {"required": f["obligation"] == "wymagane"}
            if f.get("allowed_values"):
                constraints["enum"] = [v["value"] for v in f["allowed_values"]]
            for key, ts_key in (("pattern", "pattern"), ("minimum", "minimum"), ("maximum", "maximum"),
                                ("max_length", "maxLength")):
                if f.get(key) is not None:
                    constraints[ts_key] = f[key]
            fields.append({"name": f["name"], "title": f["label"], "description": f.get("description", ""),
                           "type": f["type"], "constraints": constraints})
        return {"name": self.code, "title": self.name, "fields": fields, "missingValues": [""]}

    def csv_template(self):
        out = io.StringIO()
        writer = csv.writer(out, lineterminator="\n")
        writer.writerow(self.names)
        writer.writerow(["" if f.get("example") is None else f["example"] for f in self.fields])
        return out.getvalue()

    def document(self):
        return {
            "code": self.code, "name": self.name, "version": self.version, "description": self.description,
            "obligations": list(OBLIGATIONS), "merge": self.merge,
            "fields": [
                {"name": f["name"], "label": f["label"], "type": f["type"], "obligation": f["obligation"],
                 "required": f["obligation"] == "wymagane", "description": f.get("description", ""),
                 "example": f.get("example"), "allowed_values": f.get("allowed_values", []),
                 "pattern": f.get("pattern"), "minimum": f.get("minimum"), "maximum": f.get("maximum"),
                 "max_length": f.get("max_length"), "synonyms": f.get("synonyms", []),
                 "derivable": f.get("derivable")}
                for f in self.fields
            ],
        }

    def xlsx_bytes(self):
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Font, PatternFill

        wb = Workbook()
        ws = wb.active
        ws.title = "Schemat"
        header = ["Lp.", "Pole", "Nazwa", "Typ", "Wymagalność", "Opis", "Dozwolone wartości", "Przykład",
                  "Inne akceptowane nazwy kolumn"]
        ws.append(header)
        for cell in ws[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="1F3864")
        for i, f in enumerate(self.fields, start=1):
            ws.append([
                i, f["name"], f["label"], TYPE_LABELS_PL.get(f["type"], f["type"]), f["obligation"],
                f.get("description", ""), ", ".join(v["value"] for v in f.get("allowed_values", [])),
                "" if f.get("example") is None else str(f["example"]), ", ".join(f.get("synonyms", [])),
            ])
        for column, width in zip("ABCDEFGHI", (5, 26, 30, 16, 13, 60, 30, 24, 40)):
            ws.column_dimensions[column].width = width
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.alignment = Alignment(wrap_text=True, vertical="top")
        example = wb.create_sheet("Szablon")
        example.append(self.names)
        example.append(["" if f.get("example") is None else f["example"] for f in self.fields])
        info = wb.create_sheet("Informacje")
        for row in (("Standard", self.name), ("Kod", self.code), ("Wersja", self.version), ("Opis", self.description)):
            info.append(list(row))
        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()


def aed_definition():
    """The verified AED standard (schema.py) mirrored into the data format (display / generic API)."""
    from mcod.aed import normalize, schema

    synonyms = {}
    for standard, keys in normalize.SYNONYMS.items():
        synonyms[standard] = [k for k in keys if k != standard]
    derivable = {"id_aed": "numer wiersza", "zrodlo": "nazwa instytucji / zbioru",
                 "data_aktualizacji": "data danych zasobu", "dostep": "„nieznany”"}
    fields = []
    for f in schema.FIELDS:
        item = {
            "name": f.name, "label": f.label, "type": f.type, "obligation": f.obligation,
            "description": f.description, "example": f.example,
            "allowed_values": [{"value": v, "label": label} for v, label in f.allowed_values],
            "pattern": f.pattern, "minimum": f.minimum, "maximum": f.maximum, "max_length": f.max_length,
            "synonyms": synonyms.get(f.name, []),
        }
        if f.name in derivable:
            item["derivable"] = derivable[f.name]
        fields.append({k: v for k, v in item.items() if v is not None})
    return {
        "code": schema.SCHEMA_NAME, "name": "Dane AED – wzorcowy zakres danych", "version": schema.SCHEMA_VERSION,
        "description": schema.SCHEMA_DESCRIPTION, "fields": fields,
        "merge": {"strategy": "geo", "distance_m": 25, "loose_distance_m": 75, "similarity": 0.6,
                  "note": "zweryfikowana ścieżka AED (merge.py, DEC-011)"},
        "discovery": {"queries": ["defibrylator", "defibrylatory", "defibrylatorów", "AED"],
                      "title_pattern": "defibryl|defibryz|\\bAED\\b"},
        "publish": {"title": "Defibrylatory AED – zbiór ogólnopolski", "label_field": "nazwa",
                    "lat_field": "szerokosc_geograficzna", "lon_field": "dlugosc_geograficzna"},
    }

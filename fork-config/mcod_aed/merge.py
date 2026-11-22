"""Merge records of many source resources into one set of AEDs (ported from backend T03, DEC-011).

Two records from *different* resources are the same AED when they are ≤ 25 m apart, or ≤ 75 m
apart with similar name/address. Records of one resource are never merged with each other.
Field precedence: official (dane.gov.pl / institution) sources first, then OSM; for each field
the first non-empty value wins. Pure functions over `Rec` objects (no DB).
"""
import hashlib
import math
from collections import defaultdict
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from mcod.aed import normalize
from mcod.aed.schema import FIELD_NAMES

STRICT_M = 25.0
LOOSE_M = 75.0
SIMILARITY = 0.6
OUTLIER_KM = 30.0
CELL_DEG = 0.001
KIND_RANK = {"official": 0, "osm": 1}


@dataclass
class Rec:
    resource_id: int
    kind: str  # official | osm
    source_key: str  # stable per resource, e.g. "res40226"
    row_id: str
    data: dict
    lat: float = None
    lon: float = None
    valid: bool = True
    flags: list = field(default_factory=list)
    pk: int = None


def haversine_m(lat1, lon1, lat2, lon2):
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _label(data):
    parts = [data.get("nazwa", ""), data.get("nazwa_ulicy", ""), data.get("nr_budynku", "")]
    return normalize.norm_key(" ".join(str(p) for p in parts if p))


def similar(a, b):
    la, lb = _label(a), _label(b)
    if not la or not lb:
        return False
    return SequenceMatcher(None, la, lb).ratio() >= SIMILARITY


def flag_coordinate_problems(recs):
    """Official (municipal) sources: points far from the rest -> invalid; repeated coordinates flagged."""
    valid = [r for r in recs if r.valid]
    if len(valid) >= 3:
        lats = sorted(r.lat for r in valid)
        lons = sorted(r.lon for r in valid)
        med_lat, med_lon = lats[len(lats) // 2], lons[len(lons) // 2]
        for r in valid:
            if haversine_m(r.lat, r.lon, med_lat, med_lon) > OUTLIER_KM * 1000:
                r.valid = False
                r.flags = r.flags + ["wspolrzedne_daleko_od_pozostalych"]
    seen = defaultdict(int)
    for r in recs:
        if r.valid:
            seen[(r.lat, r.lon)] += 1
    for r in recs:
        if r.valid and seen[(r.lat, r.lon)] > 1:
            r.flags = r.flags + ["wspolrzedne_powtorzone"]


class _UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))

    def find(self, i):
        while self.parent[i] != i:
            self.parent[i] = self.parent[self.parent[i]]
            i = self.parent[i]
        return i

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[max(ra, rb)] = min(ra, rb)


def _rank(rec):
    filled = sum(1 for v in rec.data.values() if v not in (None, ""))
    return (KIND_RANK.get(rec.kind, 9), -filled, rec.source_key, rec.row_id)


def cluster(records):
    """Greedy agglomeration by distance; a cluster never holds two records of one resource."""
    grid = defaultdict(list)
    for i, rec in enumerate(records):
        grid[(int(rec.lat / CELL_DEG), int(rec.lon / CELL_DEG))].append(i)
    pairs = []
    for i, rec in enumerate(records):
        cy, cx = int(rec.lat / CELL_DEG), int(rec.lon / CELL_DEG)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                for j in grid.get((cy + dy, cx + dx), ()):
                    if j <= i:
                        continue
                    other = records[j]
                    if other.resource_id == rec.resource_id:
                        continue
                    d = haversine_m(rec.lat, rec.lon, other.lat, other.lon)
                    if d <= STRICT_M or (d <= LOOSE_M and similar(rec.data, other.data)):
                        pairs.append((d, i, j))
    pairs.sort()
    uf = _UnionFind(len(records))
    resources = {i: {r.resource_id} for i, r in enumerate(records)}
    for _, i, j in pairs:
        ri, rj = uf.find(i), uf.find(j)
        if ri == rj or resources[ri] & resources[rj]:
            continue
        uf.union(ri, rj)
        root = uf.find(ri)
        resources[root] = resources[ri] | resources[rj]
    groups = defaultdict(list)
    for i, rec in enumerate(records):
        groups[uf.find(i)].append(rec)
    return [sorted(g, key=_rank) for g in groups.values()]


def merge_group(group):
    """Common record of one cluster (+ provenance)."""
    data = {}
    for name in FIELD_NAMES:
        for rec in group:
            value = rec.data.get(name)
            if value not in (None, ""):
                data[name] = value
                break
    names, urls = [], []
    for rec in group:
        src = rec.data.get("zrodlo")
        if src and src not in names:
            names.append(src)
        url = rec.data.get("zrodlo_url")
        if url and url not in urls:
            urls.append(url)
    data["zrodlo"] = "; ".join(names)
    if urls:
        data["zrodlo_url"] = urls[0]
    dates = [r.data["data_aktualizacji"] for r in group if r.data.get("data_aktualizacji")]
    if dates:
        data["data_aktualizacji"] = max(dates)
    best = group[0]
    key = "{}:{}".format(best.source_key, best.row_id)
    id_aed = "PL-AED-" + hashlib.sha1(key.encode()).hexdigest()[:10].upper()
    data["id_aed"] = id_aed
    return id_aed, best.lat, best.lon, data


def merge(records):
    """-> list of (id_aed, lat, lon, data, member records). Only valid records are merged."""
    valid = [r for r in records if r.valid and r.lat is not None and r.lon is not None]
    result, used = [], set()
    for group in cluster(valid):
        id_aed, lat, lon, data = merge_group(group)
        while id_aed in used:
            id_aed += "X"
        data["id_aed"] = id_aed
        used.add(id_aed)
        result.append((id_aed, lat, lon, data, group))
    return result

"""Parse all selected source resources, normalize them and merge into national AEDs (T03).

Dedupe: two records from *different* resources are the same AED when they are ≤ 25 m apart,
or ≤ 75 m apart with similar name/address. Records of one resource are never merged with each
other (a publisher listing two AEDs in one building means two devices). Field precedence:
official dane.gov.pl sources first, then OSM; for each field the first non-empty value wins.
"""

from __future__ import annotations

import hashlib
import math
from collections import defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher

from django.db import transaction

from apps.aed import normalize, parsers
from apps.aed.models import AED, SourceDataset, SourceRecord, SourceResource
from apps.aed.schema import FIELD_NAMES

STRICT_M = 25.0
LOOSE_M = 75.0
SIMILARITY = 0.6
OUTLIER_KM = 30.0  # municipal datasets are local: a point this far from the rest is suspicious
CELL_DEG = 0.001  # ~111 m (lat) x ~67 m (lon in PL) grid for neighbour search
KIND_RANK = {SourceDataset.Kind.DANE_GOV_PL: 0, SourceDataset.Kind.OSM: 1}


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _label(data: dict) -> str:
    parts = [data.get("nazwa", ""), data.get("nazwa_ulicy", ""), data.get("nr_budynku", "")]
    return normalize.norm_key(" ".join(p for p in parts if p))


def similar(a: dict, b: dict) -> bool:
    la, lb = _label(a), _label(b)
    if not la or not lb:
        return False
    return SequenceMatcher(None, la, lb).ratio() >= SIMILARITY


@dataclass
class ParseResult:
    resource: SourceResource
    records: int
    valid: int
    error: str = ""


def _context(resource: SourceResource) -> normalize.SourceContext:
    ds = resource.dataset
    name = ds.publisher or ds.title
    if ds.kind == SourceDataset.Kind.OSM:
        name = "OpenStreetMap"
    return normalize.SourceContext(
        kind=ds.kind,
        key=f"{'osm' if ds.kind == 'osm' else 'dgp' + ds.external_id}",
        name=name,
        url=ds.url,
        updated=(ds.source_modified or resource.fetched_at).date()
        if (ds.source_modified or resource.fetched_at) else None,
    )


def parse_resource(resource: SourceResource) -> ParseResult:
    """(Re)build SourceRecords of one resource and store its coverage report."""
    resource.records.all().delete()
    try:
        rows = parsers.parse(resource.format, bytes(resource.raw or b""))
    except (parsers.ParseError, ValueError, KeyError) as exc:
        resource.parse_status = "error"
        resource.parse_error = str(exc)[:2000]
        resource.coverage = {}
        resource.record_count = 0
        resource.save(update_fields=["parse_status", "parse_error", "coverage", "record_count"])
        return ParseResult(resource, 0, 0, str(exc))
    ctx = _context(resource)
    objs, seen = [], set()
    for row in rows:
        result = normalize.normalize_row(row, ctx)
        row_id = row.row_id
        while row_id in seen:  # duplicate ids inside one file
            row_id += "+"
        seen.add(row_id)
        objs.append(
            SourceRecord(
                resource=resource, source_row_id=row_id[:100], raw=row.props, data=result.data,
                lat=result.lat, lon=result.lon, valid=result.valid, quality_flags=result.flags,
            )
        )
    if ctx.kind == SourceDataset.Kind.DANE_GOV_PL:
        flag_coordinate_problems(objs)
    SourceRecord.objects.bulk_create(objs, batch_size=2000)
    resource.parse_status = "ok"
    resource.parse_error = ""
    resource.record_count = len(objs)
    resource.coverage = normalize.coverage([o.data for o in objs if o.valid])
    resource.save(update_fields=["parse_status", "parse_error", "coverage", "record_count"])
    return ParseResult(resource, len(objs), sum(1 for o in objs if o.valid))


def flag_coordinate_problems(objs: list[SourceRecord]) -> None:
    """Flag coordinates repeated within one source and points far from the rest (copy-paste)."""
    valid = [o for o in objs if o.valid]
    if len(valid) >= 3:
        lats = sorted(o.lat for o in valid)
        lons = sorted(o.lon for o in valid)
        med_lat, med_lon = lats[len(lats) // 2], lons[len(lons) // 2]
        for o in valid:
            if haversine_m(o.lat, o.lon, med_lat, med_lon) > OUTLIER_KM * 1000:
                o.valid = False
                o.quality_flags = [*o.quality_flags, "wspolrzedne_daleko_od_pozostalych"]
    seen: dict[tuple[float, float], int] = defaultdict(int)
    for o in objs:
        if o.valid:
            seen[(o.lat, o.lon)] += 1
    for o in objs:
        if o.valid and seen[(o.lat, o.lon)] > 1:
            o.quality_flags = [*o.quality_flags, "wspolrzedne_powtorzone"]


class _UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))

    def find(self, i: int) -> int:
        while self.parent[i] != i:
            self.parent[i] = self.parent[self.parent[i]]
            i = self.parent[i]
        return i

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[max(ra, rb)] = min(ra, rb)


def _rank(rec: SourceRecord) -> tuple:
    ds = rec.resource.dataset
    filled = sum(1 for v in rec.data.values() if v not in (None, ""))
    return (KIND_RANK.get(ds.kind, 9), -filled, ds.external_id, rec.source_row_id)


def cluster(records: list[SourceRecord]) -> list[list[SourceRecord]]:
    """Greedy agglomeration by distance; a cluster never holds two records of one resource."""
    grid: dict[tuple[int, int], list[int]] = defaultdict(list)
    for i, rec in enumerate(records):
        grid[(int(rec.lat / CELL_DEG), int(rec.lon / CELL_DEG))].append(i)
    pairs: list[tuple[float, int, int]] = []
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
    resources: dict[int, set[int]] = {i: {r.resource_id} for i, r in enumerate(records)}
    for _, i, j in pairs:
        ri, rj = uf.find(i), uf.find(j)
        if ri == rj or resources[ri] & resources[rj]:
            continue
        uf.union(ri, rj)
        root = uf.find(ri)
        resources[root] = resources[ri] | resources[rj]
    groups: dict[int, list[SourceRecord]] = defaultdict(list)
    for i, rec in enumerate(records):
        groups[uf.find(i)].append(rec)
    return [sorted(g, key=_rank) for g in groups.values()]


def _merge_group(group: list[SourceRecord]) -> dict:
    data: dict = {}
    for name in FIELD_NAMES:
        for rec in group:
            value = rec.data.get(name)
            if value not in (None, ""):
                data[name] = value
                break
    names = []
    for rec in group:
        src = rec.data.get("zrodlo")
        if src and src not in names:
            names.append(src)
    data["zrodlo"] = "; ".join(names)
    dates = [r.data["data_aktualizacji"] for r in group if r.data.get("data_aktualizacji")]
    if dates:
        data["data_aktualizacji"] = max(dates)
    return data


def merge_all() -> dict:
    """Rebuild the national AED table from all valid SourceRecords."""
    records = list(
        SourceRecord.objects.filter(valid=True, resource__selected=True)
        .select_related("resource__dataset")
        .defer("raw", "resource__raw")  # never pull multi-MB payloads per record
        .order_by("id")
    )
    groups = cluster(records)
    with transaction.atomic():
        SourceRecord.objects.update(aed=None)
        AED.objects.all().delete()
        used: set[str] = set()
        aeds: list[AED] = []
        members: list[list[int]] = []
        for group in groups:
            best = group[0]
            ds = best.resource.dataset
            key = f"{ds.kind}:{ds.external_id}:{best.source_row_id}"
            id_aed = "PL-AED-" + hashlib.sha1(key.encode()).hexdigest()[:10].upper()
            while id_aed in used:
                id_aed += "X"
            used.add(id_aed)
            data = _merge_group(group)
            data["id_aed"] = id_aed
            aeds.append(
                AED(id_aed=id_aed, lat=best.lat, lon=best.lon, data=data, sources_count=len(group))
            )
            members.append([r.pk for r in group])
        created = AED.objects.bulk_create(aeds, batch_size=2000)
        links = []
        for aed, pks in zip(created, members, strict=True):
            links.extend((pk, aed.pk) for pk in pks)
        for start in range(0, len(links), 2000):
            batch = dict(links[start : start + 2000])
            recs = SourceRecord.objects.filter(pk__in=batch.keys()).only("pk")
            for rec in recs:
                rec.aed_id = batch[rec.pk]
            SourceRecord.objects.bulk_update(recs, ["aed"], batch_size=2000)
    merged = sum(1 for g in groups if len(g) > 1)
    return {"records": len(records), "aeds": len(groups), "merged_groups": merged}


def process_all() -> dict:
    """Parse every selected resource and merge. Returns a summary for the command output."""
    results = [
        parse_resource(r)
        for r in SourceResource.objects.filter(selected=True).select_related("dataset")
    ]
    summary = merge_all()
    summary["resources"] = results
    return summary

/**
 * dane.gov.pl fork API (T15, DEC-014) — server-side only (route handlers / Server Components).
 * `DANEGOV_API_URL` (e.g. https://api.mcod.local) is never exposed to the browser; the browser
 * uses the same-origin route `/portal-api/aed/devices`.
 */
import type { SourcesReport } from "./api";

export interface PortalLinks {
  apiUrl: string;
  datasetUrl: string | null;
}

export function getPortalApiUrl(): string | null {
  const configured = process.env.DANEGOV_API_URL?.trim();
  return configured ? configured.replace(/\/+$/, "") : null;
}

interface PortalSourceAttributes {
  resource_id: number;
  dataset_id: number;
  dataset_title: string;
  institution: string;
  source_type: string; // "official" | "osm"
  url: string | null;
  record_count: number;
}

interface PortalSourcesDocument {
  data: { id: string; attributes: PortalSourceAttributes }[];
  meta: {
    aed_count: number;
    updated_at: string | null;
    national_dataset?: { url?: string } | null;
  };
}

/** Pure mapper: portal `/1.4/aed/sources` document -> the report shape used by `DataInfo`. */
export function mapPortalSources(doc: PortalSourcesDocument): {
  report: SourcesReport;
  datasetUrl: string | null;
} {
  return {
    report: {
      aed_count: doc.meta.aed_count,
      updated_at: doc.meta.updated_at,
      sources: doc.data.map((item) => ({
        id: item.id,
        title:
          item.attributes.source_type === "osm"
            ? item.attributes.dataset_title
            : `${item.attributes.institution} – ${item.attributes.dataset_title}`,
        kind: item.attributes.source_type === "osm" ? "osm" : "dane_gov_pl",
        url: item.attributes.url,
        record_count: item.attributes.record_count,
      })),
    },
    datasetUrl: doc.meta.national_dataset?.url ?? null,
  };
}

export async function fetchPortalSources(): Promise<{
  report: SourcesReport;
  datasetUrl: string | null;
} | null> {
  const base = getPortalApiUrl();
  if (!base) return null;
  try {
    const response = await fetch(`${base}/1.4/aed/sources`, {
      headers: { Accept: "application/vnd.api+json, application/json" },
      cache: "no-store",
    });
    if (!response.ok) return null;
    return mapPortalSources((await response.json()) as PortalSourcesDocument);
  } catch {
    return null;
  }
}

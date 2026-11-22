import type { AedCollection } from "./aed";

export interface HealthResponse {
  status: "ok" | "degraded";
  database: "ok" | "error";
  timestamp: string;
}

export interface HealthCheckResult {
  ok: boolean;
  statusCode: number | null;
  data: HealthResponse | null;
  error: string | null;
}

const DEFAULT_API_URL = "http://localhost:8000";

export function getPublicApiBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (!configured) {
    return "";
  }
  return configured.replace(/\/+$/, "");
}

export function getApiBaseUrl(): string {
  if (typeof window === "undefined") {
    const internal = process.env.API_INTERNAL_URL?.trim();
    if (internal && internal.length > 0) {
      return internal.replace(/\/+$/, "");
    }
    return getPublicApiBaseUrl() || DEFAULT_API_URL;
  }
  return getPublicApiBaseUrl();
}

export async function fetchHealth(): Promise<HealthCheckResult> {
  const endpoint = `${getApiBaseUrl()}/api/health/`;

  try {
    const response = await fetch(endpoint, {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
      cache: "no-store",
    });

    const contentType = response.headers.get("content-type") ?? "";
    const isJson = contentType.includes("application/json");
    const data = isJson ? ((await response.json()) as HealthResponse) : null;

    if (!response.ok) {
      return {
        ok: false,
        statusCode: response.status,
        data,
        error: `Backend responded with HTTP ${response.status}.`,
      };
    }

    return {
      ok: data?.status === "ok" && data?.database === "ok",
      statusCode: response.status,
      data,
      error: null,
    };
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "Unable to reach the Django API service.";
    return {
      ok: false,
      statusCode: null,
      data: null,
      error: message,
    };
  }
}

// --- T07: AED map ------------------------------------------------------------

export interface SourceSummary {
  id: string;
  title: string;
  kind: string; // "dane_gov_pl" | "osm"
  url: string | null;
  record_count: number;
}

export interface SourcesReport {
  aed_count: number;
  updated_at: string | null;
  sources: SourceSummary[];
}

/** National AED set as GeoJSON (DEC-008); browser -> same-origin route -> dane.gov.pl fork API (T15). */
export async function fetchAeds(signal?: AbortSignal): Promise<AedCollection> {
  const response = await fetch("/portal-api/aed/devices", {
    headers: { Accept: "application/geo+json, application/json" },
    signal,
  });
  if (!response.ok) {
    throw new Error(`Backend responded with HTTP ${response.status}.`);
  }
  return (await response.json()) as AedCollection;
}

/** Counts + harvested sources for the "Skąd są te dane?" section (server-side). `null` on error. */
export async function fetchSources(): Promise<SourcesReport | null> {
  try {
    const response = await fetch(`${getApiBaseUrl()}/api/sources/`, {
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    if (!response.ok) return null;
    const data = (await response.json()) as SourcesReport;
    return {
      aed_count: data.aed_count,
      updated_at: data.updated_at,
      sources: (data.sources ?? []).map((source) => ({
        id: source.id,
        title: source.title,
        kind: source.kind,
        url: source.url,
        record_count: source.record_count,
      })),
    };
  } catch {
    return null;
  }
}

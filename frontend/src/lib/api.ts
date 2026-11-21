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

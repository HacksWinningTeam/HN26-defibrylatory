import { getApiBaseUrl } from "@/lib/api";
import { getPortalApiUrl } from "@/lib/portal";

export const dynamic = "force-dynamic";

/**
 * Same-origin AED GeoJSON for the map (T15): from the dane.gov.pl fork (`/1.4/aed/devices`) when
 * `DANEGOV_API_URL` is set, otherwise from our old backend (`/api/aed/`, same DEC-008 contract).
 */
export async function GET() {
  const portal = getPortalApiUrl();
  const upstream = portal ? `${portal}/1.4/aed/devices` : `${getApiBaseUrl()}/api/aed/`;
  try {
    const response = await fetch(upstream, {
      headers: { Accept: "application/geo+json, application/json" },
      cache: "no-store",
    });
    if (!response.ok) {
      return Response.json(
        { error: `Upstream responded with HTTP ${response.status}.` },
        { status: 502 },
      );
    }
    return new Response(await response.arrayBuffer(), {
      status: 200,
      headers: {
        "Content-Type": "application/geo+json; charset=utf-8",
        "Cache-Control": "no-store",
        "X-AED-Data-Source": portal ? "dane.gov.pl fork" : "backend",
      },
    });
  } catch (error) {
    console.error("AED data source unreachable", upstream, error);
    return Response.json({ error: "AED data source unreachable." }, { status: 502 });
  }
}

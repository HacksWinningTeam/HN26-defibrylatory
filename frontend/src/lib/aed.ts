/**
 * Pure AED logic for the "Najbliższy AED" page (T07, DEC-008 / DEC-010).
 * No React / DOM / Leaflet imports here so it can be unit-tested with node --test.
 */

export interface AedSource {
  nazwa: string;
  typ: string; // "dane_gov_pl" | "osm"
  url: string | null;
}

export interface AedProperties {
  id_aed: string;
  nazwa: string | null;
  adres: string | null;
  miejscowosc: string | null;
  opis_lokalizacji: string | null;
  w_budynku: boolean | null;
  pietro: number | string | null;
  dostep: string | null;
  godziny_dostepnosci: string | null;
  zabezpieczenie: string | null;
  status: string | null;
  dysponent: string | null;
  telefon_kontaktowy: string | null;
  data_aktualizacji: string | null;
  zrodla: AedSource[];
}

export interface AedFeature {
  type: "Feature";
  id: string;
  geometry: { type: "Point"; coordinates: [number, number] };
  properties: AedProperties;
}

export interface AedCollection {
  type: "FeatureCollection";
  meta: { count: number; generated_at: string; license: string };
  features: AedFeature[];
}

export interface LatLon {
  lat: number;
  lon: number;
}

export interface UserLocation extends LatLon {
  label: string;
  /** true = the hardcoded hackathon venue (always labelled as demo in the UI). */
  isDemo: boolean;
}

export interface NearbyAed {
  /** 1-based rank, also the number on the map pin. */
  rank: number;
  feature: AedFeature;
  distanceM: number;
}

/** Hackathon venue (OSM / Nominatim), DEC-010. */
export const DEMO_LOCATION: UserLocation = {
  lat: 53.170719,
  lon: 18.047651,
  label: "Bydgoskie Centrum Targowo-Wystawiennicze, Bydgoszcz",
  isDemo: true,
};

/** Above this distance the UI adds "far away – call 112" (DEC-010). */
export const FAR_AWAY_M = 2000;

/** Average walking speed used for the "ok. N min pieszo" estimate. */
export const WALK_M_PER_MIN = 80;

type SearchParamValue = string | string[] | undefined;

function firstParam(value: SearchParamValue): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

function parseCoordinate(value: SearchParamValue, limit: number): number | null {
  const raw = firstParam(value)?.trim().replace(",", ".");
  if (!raw || !/^-?\d+(\.\d+)?$/.test(raw)) return null;
  const parsed = Number(raw);
  return Number.isFinite(parsed) && Math.abs(parsed) <= limit ? parsed : null;
}

/**
 * `/?lat=..&lon=..&miejsce=..` override for demos elsewhere; anything invalid falls
 * back to the demo location.
 */
export function parseLocationParams(
  params: Record<string, SearchParamValue>,
): UserLocation {
  const lat = parseCoordinate(params.lat, 90);
  const lon = parseCoordinate(params.lon, 180);
  if (lat === null || lon === null) return DEMO_LOCATION;
  const place = firstParam(params.miejsce)?.trim().slice(0, 120);
  return {
    lat,
    lon,
    label: place || `${lat.toFixed(5)}, ${lon.toFixed(5)}`,
    isDemo: false,
  };
}

const EARTH_RADIUS_M = 6371008.8;

export function haversineMeters(a: LatLon, b: LatLon): number {
  const toRad = (deg: number) => (deg * Math.PI) / 180;
  const dLat = toRad(b.lat - a.lat);
  const dLon = toRad(b.lon - a.lon);
  const h =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(a.lat)) * Math.cos(toRad(b.lat)) * Math.sin(dLon / 2) ** 2;
  return 2 * EARTH_RADIUS_M * Math.asin(Math.min(1, Math.sqrt(h)));
}

export function featureLatLon(feature: AedFeature): LatLon {
  const [lon, lat] = feature.geometry.coordinates;
  return { lat, lon };
}

export function nearestAeds(
  features: readonly AedFeature[],
  from: LatLon,
  count: number,
): NearbyAed[] {
  if (count <= 0) return [];
  const best: { feature: AedFeature; distanceM: number }[] = [];
  for (const feature of features) {
    const coords = feature.geometry?.coordinates;
    if (!coords || !Number.isFinite(coords[0]) || !Number.isFinite(coords[1])) continue;
    const distanceM = haversineMeters(from, featureLatLon(feature));
    if (best.length < count || distanceM < best[best.length - 1].distanceM) {
      best.push({ feature, distanceM });
      best.sort((x, y) => x.distanceM - y.distanceM);
      if (best.length > count) best.pop();
    }
  }
  return best.map((item, index) => ({ rank: index + 1, ...item }));
}

/** `180 m` / `1,2 km` (pl) / `1.2 km` (en); rounded to 10 m below 1 km. */
export function formatDistance(meters: number, locale: string): string {
  if (meters < 1000) return `${Math.max(10, Math.round(meters / 10) * 10)} m`;
  const km = meters / 1000;
  const formatted = new Intl.NumberFormat(locale, {
    maximumFractionDigits: km < 10 ? 1 : 0,
    minimumFractionDigits: km < 10 ? 1 : 0,
  }).format(km);
  return `${formatted} km`;
}

export function walkingMinutes(meters: number): number {
  return Math.max(1, Math.round(meters / WALK_M_PER_MIN));
}

export function is247(hours: string | null | undefined): boolean {
  if (!hours) return false;
  const value = hours.trim().toLowerCase();
  return value === "24/7" || value.startsWith("24/7") || value.includes("całodob");
}

export type BadgeKind =
  | "locked"
  | "code"
  | "public"
  | "restricted"
  | "private"
  | "access-unknown"
  | "h24"
  | "out-of-service";

export type BadgeVariant = "neutral" | "success" | "warning" | "error";

export const BADGE_VARIANTS: Record<BadgeKind, BadgeVariant> = {
  locked: "warning",
  code: "warning",
  public: "success",
  restricted: "warning",
  private: "error",
  "access-unknown": "neutral",
  h24: "success",
  "out-of-service": "error",
};

const OUT_OF_SERVICE = new Set(["niesprawny", "w_serwisie", "skradziony", "wycofany"]);

/** Max 3 badges; priority: lock/code -> access -> 24/7 -> out of service (DEC-010). */
export function topBadges(props: AedProperties, max = 3): BadgeKind[] {
  const badges: BadgeKind[] = [];
  if (props.status && OUT_OF_SERVICE.has(props.status)) badges.push("out-of-service");
  if (props.zabezpieczenie === "zamkniety_na_klucz") badges.push("locked");
  else if (props.zabezpieczenie === "szafka_na_kod") badges.push("code");
  if (props.dostep === "publiczny") badges.push("public");
  else if (props.dostep === "ograniczony") badges.push("restricted");
  else if (props.dostep === "prywatny") badges.push("private");
  else badges.push("access-unknown");
  if (is247(props.godziny_dostepnosci)) badges.push("h24");
  // "out of service" is safety-critical: keep it even when the list is cut.
  return badges.slice(0, max);
}

/** OSM walking route from the (demo) location to the AED, opened in a new tab. */
export function osmDirectionsUrl(from: LatLon, to: LatLon): string {
  const route = `${from.lat}%2C${from.lon}%3B${to.lat}%2C${to.lon}`;
  return `https://www.openstreetmap.org/directions?engine=fossgis_osrm_foot&route=${route}`;
}

/** Card / popup title: name, else location description, else null (UI shows "Defibrylator AED"). */
export function aedTitle(props: AedProperties): string | null {
  return props.nazwa?.trim() || props.opis_lokalizacji?.trim() || null;
}

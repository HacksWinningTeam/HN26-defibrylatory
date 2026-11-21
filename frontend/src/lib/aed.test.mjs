import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import Module, { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const require = createRequire(import.meta.url);
const src = fileURLToPath(new URL("../", import.meta.url));
for (const extension of [".ts", ".tsx"]) {
  Module._extensions[extension] = (mod, filename) =>
    mod._compile(
      ts.transpileModule(fs.readFileSync(filename, "utf8"), {
        compilerOptions: {
          module: ts.ModuleKind.CommonJS,
          jsx: ts.JsxEmit.ReactJSX,
          esModuleInterop: true,
          target: ts.ScriptTarget.ES2020,
        },
      }).outputText,
      filename,
    );
}

const resolve = Module._resolveFilename;
Module._resolveFilename = function (request, ...args) {
  return resolve.call(
    this,
    request.startsWith("@/") ? path.join(src, request.slice(2)) : request,
    ...args,
  );
};

const {
  DEMO_LOCATION,
  FAR_AWAY_M,
  parseLocationParams,
  haversineMeters,
  nearestAeds,
  formatDistance,
  walkingMinutes,
  is247,
  topBadges,
  osmDirectionsUrl,
  aedTitle,
} = require("./aed.ts");

function props(overrides = {}) {
  return {
    id_aed: "PL-AED-1",
    nazwa: null,
    adres: null,
    miejscowosc: null,
    opis_lokalizacji: null,
    w_budynku: null,
    pietro: null,
    dostep: null,
    godziny_dostepnosci: null,
    zabezpieczenie: null,
    status: null,
    dysponent: null,
    telefon_kontaktowy: null,
    data_aktualizacji: null,
    zrodla: [],
    ...overrides,
  };
}

function feature(id, lat, lon, overrides = {}) {
  return {
    type: "Feature",
    id,
    geometry: { type: "Point", coordinates: [lon, lat] },
    properties: props({ id_aed: id, ...overrides }),
  };
}

test("demo location is the BCTW Bydgoszcz venue and flagged as demo", () => {
  assert.equal(DEMO_LOCATION.lat, 53.170719);
  assert.equal(DEMO_LOCATION.lon, 18.047651);
  assert.equal(DEMO_LOCATION.isDemo, true);
  assert.equal(FAR_AWAY_M, 2000);
});

test("parseLocationParams accepts valid overrides and falls back otherwise", () => {
  assert.deepEqual(parseLocationParams({}), DEMO_LOCATION);
  assert.deepEqual(parseLocationParams({ lat: "abc", lon: "18" }), DEMO_LOCATION);
  assert.deepEqual(parseLocationParams({ lat: "95", lon: "18" }), DEMO_LOCATION);
  assert.deepEqual(parseLocationParams({ lat: "52.2", lon: "" }), DEMO_LOCATION);
  assert.deepEqual(parseLocationParams({ lat: "52,2297", lon: "21.0122", miejsce: " Warszawa " }), {
    lat: 52.2297,
    lon: 21.0122,
    label: "Warszawa",
    isDemo: false,
  });
  const noName = parseLocationParams({ lat: ["50.06143"], lon: ["19.93658"] });
  assert.equal(noName.label, "50.06143, 19.93658");
  assert.equal(noName.isDemo, false);
});

test("haversineMeters matches known distances", () => {
  const warsaw = { lat: 52.2297, lon: 21.0122 };
  const krakow = { lat: 50.0647, lon: 19.945 };
  const d = haversineMeters(warsaw, krakow);
  assert.ok(Math.abs(d - 252_000) < 2_000, `got ${d}`);
  assert.equal(haversineMeters(warsaw, warsaw), 0);
});

test("nearestAeds returns the n closest, ranked, skipping invalid geometry", () => {
  const from = { lat: 53.17, lon: 18.05 };
  const features = [
    feature("far", 54.0, 18.05),
    feature("near", 53.171, 18.05),
    feature("mid", 53.18, 18.05),
    { ...feature("broken", 0, 0), geometry: { type: "Point", coordinates: [Number.NaN, 1] } },
    feature("nearest", 53.1701, 18.05),
  ];
  const result = nearestAeds(features, from, 3);
  assert.deepEqual(result.map((r) => r.feature.id), ["nearest", "near", "mid"]);
  assert.deepEqual(result.map((r) => r.rank), [1, 2, 3]);
  assert.ok(result[0].distanceM < result[1].distanceM);
  assert.deepEqual(nearestAeds(features, from, 0), []);
  assert.equal(nearestAeds([], from, 5).length, 0);
});

test("formatDistance and walkingMinutes", () => {
  assert.equal(formatDistance(183, "pl-PL"), "180 m");
  assert.equal(formatDistance(3, "pl-PL"), "10 m");
  assert.equal(formatDistance(1234, "pl-PL"), "1,2 km");
  assert.equal(formatDistance(1234, "en-US"), "1.2 km");
  assert.equal(formatDistance(15_400, "en-US"), "15 km");
  assert.equal(walkingMinutes(10), 1);
  assert.equal(walkingMinutes(180), 2);
  assert.equal(walkingMinutes(800), 10);
});

test("is247 recognises round-the-clock access", () => {
  assert.equal(is247("24/7"), true);
  assert.equal(is247(" 24/7 "), true);
  assert.equal(is247("24/7; PH off"), true);
  assert.equal(is247("Całodobowo"), true);
  assert.equal(is247("Mo-Fr 08:00-16:00"), false);
  assert.equal(is247(null), false);
});

test("topBadges: max 3, priority lock/code -> access -> 24/7, out of service first", () => {
  assert.deepEqual(topBadges(props()), ["access-unknown"]);
  assert.deepEqual(
    topBadges(props({ dostep: "publiczny", godziny_dostepnosci: "24/7" })),
    ["public", "h24"],
  );
  assert.deepEqual(
    topBadges(props({ zabezpieczenie: "zamkniety_na_klucz", dostep: "ograniczony", godziny_dostepnosci: "24/7" })),
    ["locked", "restricted", "h24"],
  );
  assert.deepEqual(
    topBadges(props({ status: "niesprawny", zabezpieczenie: "szafka_na_kod", dostep: "prywatny", godziny_dostepnosci: "24/7" })),
    ["out-of-service", "code", "private"],
  );
  assert.deepEqual(topBadges(props({ status: "sprawny", dostep: "nieznany" })), ["access-unknown"]);
});

test("osmDirectionsUrl builds a walking route from the location to the AED", () => {
  assert.equal(
    osmDirectionsUrl({ lat: 53.170719, lon: 18.047651 }, { lat: 53.171, lon: 18.05 }),
    "https://www.openstreetmap.org/directions?engine=fossgis_osrm_foot&route=53.170719%2C18.047651%3B53.171%2C18.05",
  );
});

test("aedTitle prefers the name, then the location description", () => {
  assert.equal(aedTitle(props({ nazwa: " AED Hala A ", opis_lokalizacji: "x" })), "AED Hala A");
  assert.equal(aedTitle(props({ nazwa: "", opis_lokalizacji: "przy recepcji" })), "przy recepcji");
  assert.equal(aedTitle(props()), null);
});

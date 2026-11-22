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

const { mapPortalSources, getPortalApiUrl } = require("./portal.ts");

test("mapPortalSources maps the portal /1.4/aed/sources document to the DataInfo report", () => {
  const doc = {
    data: [
      { id: "40226", attributes: { resource_id: 40226, dataset_id: 4219, dataset_title: "Defibrylatory w Krośnie",
        institution: "Urząd Miasta Krosna", source_type: "official", url: "https://mcod.local/pl/dataset/4219", record_count: 21 } },
      { id: "40231", attributes: { resource_id: 40231, dataset_id: 4224, dataset_title: "OpenStreetMap – AED",
        institution: "OSM", source_type: "osm", url: "https://mcod.local/pl/dataset/4224", record_count: 18310 } },
    ],
    meta: { aed_count: 18776, updated_at: "2026-11-22T01:22:03Z",
      national_dataset: { url: "https://mcod.local/pl/dataset/4211,x" } },
  };
  const { report, datasetUrl } = mapPortalSources(doc);
  assert.equal(report.aed_count, 18776);
  assert.equal(report.updated_at, "2026-11-22T01:22:03Z");
  assert.deepEqual(report.sources[0], { id: "40226", title: "Urząd Miasta Krosna – Defibrylatory w Krośnie",
    kind: "dane_gov_pl", url: "https://mcod.local/pl/dataset/4219", record_count: 21 });
  assert.equal(report.sources[1].kind, "osm");
  assert.equal(report.sources[1].title, "OpenStreetMap – AED");
  assert.equal(datasetUrl, "https://mcod.local/pl/dataset/4211,x");
  assert.equal(mapPortalSources({ data: [], meta: { aed_count: 0, updated_at: null } }).datasetUrl, null);
});

test("getPortalApiUrl reads DANEGOV_API_URL and trims trailing slashes", () => {
  const previous = process.env.DANEGOV_API_URL;
  process.env.DANEGOV_API_URL = " https://api.mcod.local/ ";
  assert.equal(getPortalApiUrl(), "https://api.mcod.local");
  process.env.DANEGOV_API_URL = "";
  assert.equal(getPortalApiUrl(), null);
  if (previous === undefined) delete process.env.DANEGOV_API_URL;
  else process.env.DANEGOV_API_URL = previous;
});

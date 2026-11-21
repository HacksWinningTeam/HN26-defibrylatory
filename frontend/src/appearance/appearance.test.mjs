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
  appearances,
  defaultAppearance,
  isAppearance,
  resolveAppearance,
} = require("./appearance.ts");
const { getPrehydrateScript } = require("../lib/prehydrate.ts");

test("resolveAppearance accepts valid values and falls back to defaultAppearance", () => {
  assert.deepEqual(appearances, [
    "system",
    "light",
    "dark",
    "hc-black-white",
    "hc-black-yellow",
    "grayscale",
  ]);
  assert.equal(resolveAppearance("light"), "light");
  assert.equal(resolveAppearance("dark"), "dark");
  assert.equal(resolveAppearance("system"), "system");
  assert.equal(resolveAppearance("hc-black-white"), "hc-black-white");
  assert.equal(resolveAppearance("hc-black-yellow"), "hc-black-yellow");
  assert.equal(resolveAppearance("grayscale"), "grayscale");
  assert.equal(resolveAppearance("sepia"), defaultAppearance);
  assert.equal(resolveAppearance(undefined), defaultAppearance);
  assert.equal(isAppearance("dark"), true);
  assert.equal(isAppearance("auto"), false);
});

test("getPrehydrateScript includes storage keys and valid syntax", () => {
  const script = getPrehydrateScript();
  assert.match(script, /hn26-appearance/);
  assert.match(script, /hn26-locale/);
  assert.doesNotThrow(() => new Function(script));
});

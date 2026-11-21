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

const { english, polish } = require("./messages.ts");
const { defaultLocale, isLocale, resolveLocale } = require("./locale.ts");
const { createTranslator, translateModelMessage } = require("./translate.ts");

function placeholders(text) {
  return [...text.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();
}

test("catalog parity: every Polish message has identical placeholders and non-empty text", () => {
  for (const [key, pl] of Object.entries(polish)) {
    assert.equal(typeof pl, "string");
    assert.ok(pl.trim().length > 0, `Empty Polish translation for "${key}"`);
    assert.deepEqual(
      placeholders(pl),
      placeholders(key),
      `Placeholder mismatch for "${key}"`,
    );
    assert.equal(english[key], key);
  }
});

test("resolveLocale falls back to defaultLocale for invalid values", () => {
  assert.equal(defaultLocale, "pl-PL");
  assert.equal(resolveLocale("pl-PL"), "pl-PL");
  assert.equal(resolveLocale("en-US"), "en-US");
  assert.equal(resolveLocale("de-DE"), defaultLocale);
  assert.equal(resolveLocale(null), defaultLocale);
  assert.equal(isLocale("pl-PL"), true);
  assert.equal(isLocale("fr-FR"), false);
});

test("createTranslator interpolates parameters and translates to Polish", () => {
  const tEn = createTranslator("en-US");
  const tPl = createTranslator("pl-PL");

  assert.equal(tEn("API Status: {0}", { 0: "Healthy" }), "API Status: Healthy");
  assert.equal(tPl("API Status: {0}", { 0: "Sprawne" }), "Status API: Sprawne");
  assert.equal(tPl("Appearance"), "Wygląd");
  assert.equal(tPl("Language"), "Język");
});

test("translateModelMessage leaves unknown messages unchanged", () => {
  assert.equal(translateModelMessage("pl-PL", "Healthy"), "Sprawne");
  assert.equal(translateModelMessage("pl-PL", "Custom User Label"), "Custom User Label");
});

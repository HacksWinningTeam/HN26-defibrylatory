import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import Module, { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const require = createRequire(import.meta.url);
const src = fileURLToPath(new URL("../../", import.meta.url));
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
  APPEARANCE_PREFERENCES,
  DEFAULT_ACCESSIBILITY_PREFERENCES,
  TEXT_SCALES,
  parseAccessibilityPreferences,
  resolveTheme,
} = require("./preferences.ts");
const { getPrehydrateScript } = require("../../lib/prehydrate.ts");

test("parseAccessibilityPreferences validates and falls back cleanly", () => {
  assert.deepEqual(
    parseAccessibilityPreferences(null),
    DEFAULT_ACCESSIBILITY_PREFERENCES,
  );
  assert.deepEqual(
    parseAccessibilityPreferences(null, "hc-black-yellow"),
    {
      appearance: "hc-black-yellow",
      textScale: 100,
      underlineLinks: false,
    },
  );
  assert.deepEqual(
    parseAccessibilityPreferences(
      JSON.stringify({
        appearance: "grayscale",
        textScale: 150,
        underlineLinks: true,
      }),
    ),
    {
      appearance: "grayscale",
      textScale: 150,
      underlineLinks: true,
    },
  );
  assert.deepEqual(
    parseAccessibilityPreferences(
      JSON.stringify({
        appearance: "invalid",
        textScale: 999,
        underlineLinks: "yes",
      }),
    ),
    DEFAULT_ACCESSIBILITY_PREFERENCES,
  );
});

test("resolveTheme resolves system against OS dark preference", () => {
  assert.equal(resolveTheme("system", true), "dark");
  assert.equal(resolveTheme("system", false), "light");
  assert.equal(resolveTheme("hc-black-white", false), "hc-black-white");
  assert.ok(APPEARANCE_PREFERENCES.includes("hc-black-yellow"));
  assert.ok(TEXT_SCALES.includes(200));
});

test("getPrehydrateScript handles accessibility preferences and valid JS", () => {
  const script = getPrehydrateScript();
  assert.match(script, /hn26-accessibility/);
  assert.match(script, /textScale/);
  assert.match(script, /underlineLinks/);
  assert.doesNotThrow(() => new Function(script));
});

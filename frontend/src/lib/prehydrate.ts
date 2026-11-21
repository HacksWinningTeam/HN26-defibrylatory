import {
  appearances,
  appearanceStorageKey,
  themeColors,
} from "@/appearance/appearance";
import {
  ACCESSIBILITY_STORAGE_KEY,
  TEXT_SCALES,
} from "@/components/accessibility/preferences";
import { defaultLocale, locales, localeStorageKey } from "@/i18n/locale";

/**
 * Synchronous pre-paint script run in `<head>` before `<body>` parses.
 * Prevents flashing default appearance, text scale, link underlines, or
 * default locale when persisted browser preferences differ from SSR defaults.
 */
export function getPrehydrateScript(): string {
  const nonDefaultLocales = locales.filter(
    (locale) => locale !== defaultLocale,
  );
  return (
    `(function(){try{` +
    `var r=document.documentElement;` +
    `var raw=localStorage.getItem(${JSON.stringify(ACCESSIBILITY_STORAGE_KEY)});` +
    `var p=null;if(raw){try{p=JSON.parse(raw);}catch{}}` +
    `var a=(p&&p.appearance)||localStorage.getItem(${JSON.stringify(appearanceStorageKey)})||"system";` +
    `if(${JSON.stringify(appearances)}.indexOf(a)===-1)a="system";` +
    `var dark=window.matchMedia&&window.matchMedia("(prefers-color-scheme: dark)").matches;` +
    `var resolved=a==="system"?(dark?"dark":"light"):a;` +
    `r.dataset.appearance=resolved;` +
    `var ts=p&&p.textScale;` +
    `if(${JSON.stringify(TEXT_SCALES)}.indexOf(ts)!==-1)r.dataset.textScale=String(ts);` +
    `if(p&&typeof p.underlineLinks==="boolean")r.dataset.underlineLinks=String(p.underlineLinks);` +
    `var tc=${JSON.stringify(themeColors)};` +
    `if(tc[resolved]){var ms=document.querySelectorAll('meta[name="theme-color"]');for(var j=0;j<ms.length;j++)ms[j].content=tc[resolved];}` +
    `var l=localStorage.getItem(${JSON.stringify(localeStorageKey)});` +
    `if(${JSON.stringify(nonDefaultLocales)}.indexOf(l)!==-1){` +
    `r.lang=l;r.dataset.localePending="true";` +
    `setTimeout(function(){delete r.dataset.localePending;},2000);` +
    `}` +
    `}catch{}})();`
  );
}

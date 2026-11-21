export const appearances = [
  "system",
  "light",
  "dark",
  "hc-black-white",
  "hc-black-yellow",
  "grayscale",
] as const;

export type Appearance = (typeof appearances)[number];

export const defaultAppearance: Appearance = "system";
export const appearanceStorageKey = "hn26-appearance";
export const themeColors = {
  light: "#f8fafc",
  dark: "#0f172a",
  "hc-black-white": "#000000",
  "hc-black-yellow": "#000000",
  grayscale: "#f4f4f5",
} as const;

export function isAppearance(value: unknown): value is Appearance {
  return (
    typeof value === "string" &&
    (appearances as readonly string[]).includes(value)
  );
}

export function resolveAppearance(value: unknown): Appearance {
  return isAppearance(value) ? value : defaultAppearance;
}

export function syncThemeColorMeta(appearance: Appearance): void {
  if (
    typeof document === "undefined" ||
    typeof document.querySelectorAll !== "function"
  ) {
    return;
  }
  const metas = document.querySelectorAll<HTMLMetaElement>(
    'meta[name="theme-color"]',
  );
  for (const meta of metas) {
    if (appearance === "system") {
      const media = meta.getAttribute("media") ?? "";
      meta.content = media.includes("dark")
        ? themeColors.dark
        : themeColors.light;
    } else {
      meta.content = themeColors[appearance];
    }
  }
}

export const locales = ["en-US", "pl-PL"] as const;
export type Locale = (typeof locales)[number];

export const defaultLocale: Locale = "pl-PL";
export const localeStorageKey = "hn26-locale";

export function isLocale(value: unknown): value is Locale {
  return value === "en-US" || value === "pl-PL";
}

export function resolveLocale(value: unknown): Locale {
  return isLocale(value) ? value : defaultLocale;
}

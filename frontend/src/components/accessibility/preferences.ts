import {
  appearances,
  defaultAppearance,
  isAppearance,
  type Appearance,
} from "@/appearance/appearance";

export const TEXT_SCALES = [
  25, 50, 75, 100, 112.5, 125, 150, 175, 200,
] as const;

export type TextScale = (typeof TEXT_SCALES)[number];
export type AppearancePreference = Appearance;

export type AccessibilityPreferences = {
  appearance: AppearancePreference;
  textScale: TextScale;
  underlineLinks: boolean;
};

export const APPEARANCE_PREFERENCES = appearances;
export const ACCESSIBILITY_STORAGE_KEY = "hn26-accessibility";
export const DEFAULT_ACCESSIBILITY_PREFERENCES: AccessibilityPreferences = {
  appearance: defaultAppearance,
  textScale: 100,
  underlineLinks: false,
};

export function isTextScale(value: unknown): value is TextScale {
  return (
    typeof value === "number" &&
    (TEXT_SCALES as readonly number[]).includes(value)
  );
}

export function parseAccessibilityPreferences(
  raw: string | null,
  fallbackAppearance?: string | null,
): AccessibilityPreferences {
  if (!raw) {
    return {
      ...DEFAULT_ACCESSIBILITY_PREFERENCES,
      appearance: isAppearance(fallbackAppearance)
        ? fallbackAppearance
        : DEFAULT_ACCESSIBILITY_PREFERENCES.appearance,
    };
  }
  try {
    const parsed: unknown = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object") {
      return DEFAULT_ACCESSIBILITY_PREFERENCES;
    }
    const prefs = parsed as Partial<AccessibilityPreferences>;
    return {
      appearance: isAppearance(prefs.appearance)
        ? prefs.appearance
        : DEFAULT_ACCESSIBILITY_PREFERENCES.appearance,
      textScale: isTextScale(prefs.textScale)
        ? prefs.textScale
        : DEFAULT_ACCESSIBILITY_PREFERENCES.textScale,
      underlineLinks:
        typeof prefs.underlineLinks === "boolean"
          ? prefs.underlineLinks
          : DEFAULT_ACCESSIBILITY_PREFERENCES.underlineLinks,
    };
  } catch {
    return DEFAULT_ACCESSIBILITY_PREFERENCES;
  }
}

export function resolveTheme(
  appearance: AppearancePreference,
  prefersDark: boolean,
): Exclude<AppearancePreference, "system"> {
  if (appearance !== "system") return appearance;
  return prefersDark ? "dark" : "light";
}

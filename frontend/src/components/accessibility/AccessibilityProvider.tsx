"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useLayoutEffect,
  useMemo,
  useSyncExternalStore,
  type ReactNode,
} from "react";
import {
  appearanceStorageKey,
  syncThemeColorMeta,
} from "@/appearance/appearance";
import { readPreference, savePreference, subscribeToPreferences } from "@/lib/browser-preference";
import {
  ACCESSIBILITY_STORAGE_KEY,
  DEFAULT_ACCESSIBILITY_PREFERENCES,
  parseAccessibilityPreferences,
  resolveTheme,
  type AccessibilityPreferences,
  type AppearancePreference,
  type TextScale,
} from "./preferences";

type AccessibilityContextValue = AccessibilityPreferences & {
  setAppearance: (appearance: AppearancePreference) => void;
  setTextScale: (textScale: TextScale) => void;
  setUnderlineLinks: (underlineLinks: boolean) => void;
  resetTextScale: () => void;
  resetSettings: () => void;
};

const AccessibilityContext = createContext<AccessibilityContextValue | null>(
  null,
);

let cachedRaw: string | null | undefined;
let cachedAppearanceRaw: string | null | undefined;
let cachedPrefs: AccessibilityPreferences = DEFAULT_ACCESSIBILITY_PREFERENCES;

function getClientPreferences(): AccessibilityPreferences {
  const raw = readPreference(ACCESSIBILITY_STORAGE_KEY);
  const appearanceRaw = readPreference(appearanceStorageKey);
  if (raw === cachedRaw && appearanceRaw === cachedAppearanceRaw) {
    return cachedPrefs;
  }
  cachedRaw = raw;
  cachedAppearanceRaw = appearanceRaw;
  cachedPrefs = parseAccessibilityPreferences(raw, appearanceRaw);
  return cachedPrefs;
}

function storePreferences(preferences: AccessibilityPreferences): void {
  cachedRaw = JSON.stringify(preferences);
  cachedAppearanceRaw = preferences.appearance;
  cachedPrefs = preferences;
  savePreference(ACCESSIBILITY_STORAGE_KEY, cachedRaw);
  savePreference(appearanceStorageKey, preferences.appearance);
}

function applyPreferences(preferences: AccessibilityPreferences): void {
  if (typeof document === "undefined") return;
  const root = document.documentElement;
  const prefersDark =
    typeof window !== "undefined" &&
    window.matchMedia("(prefers-color-scheme: dark)").matches;
  const resolvedTheme = resolveTheme(preferences.appearance, prefersDark);

  root.dataset.appearance = resolvedTheme;
  root.dataset.textScale = String(preferences.textScale);
  root.dataset.underlineLinks = String(preferences.underlineLinks);
  syncThemeColorMeta(preferences.appearance);
}

export function AccessibilityProvider({ children }: { children: ReactNode }) {
  const preferences = useSyncExternalStore(
    subscribeToPreferences,
    getClientPreferences,
    () => DEFAULT_ACCESSIBILITY_PREFERENCES,
  );

  useLayoutEffect(() => {
    applyPreferences(preferences);
  }, [preferences]);

  useEffect(() => {
    if (preferences.appearance !== "system") return;
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => applyPreferences(preferences);
    mediaQuery.addEventListener("change", onChange);
    return () => mediaQuery.removeEventListener("change", onChange);
  }, [preferences]);

  const setAppearance = useCallback((appearance: AppearancePreference) => {
    storePreferences({ ...getClientPreferences(), appearance });
  }, []);

  const setTextScale = useCallback((textScale: TextScale) => {
    storePreferences({ ...getClientPreferences(), textScale });
  }, []);

  const setUnderlineLinks = useCallback((underlineLinks: boolean) => {
    storePreferences({ ...getClientPreferences(), underlineLinks });
  }, []);

  const resetTextScale = useCallback(() => {
    setTextScale(DEFAULT_ACCESSIBILITY_PREFERENCES.textScale);
  }, [setTextScale]);

  const resetSettings = useCallback(() => {
    storePreferences(DEFAULT_ACCESSIBILITY_PREFERENCES);
  }, []);

  const value = useMemo(
    () => ({
      ...preferences,
      setAppearance,
      setTextScale,
      setUnderlineLinks,
      resetTextScale,
      resetSettings,
    }),
    [
      preferences,
      resetSettings,
      resetTextScale,
      setAppearance,
      setTextScale,
      setUnderlineLinks,
    ],
  );

  return (
    <AccessibilityContext value={value}>{children}</AccessibilityContext>
  );
}

export function useAccessibilityPreferences(): AccessibilityContextValue {
  const context = useContext(AccessibilityContext);
  if (!context) {
    throw new Error(
      "useAccessibilityPreferences must be used within AccessibilityProvider.",
    );
  }
  return context;
}

"use client";

import {
  createContext,
  useContext,
  useLayoutEffect,
  useSyncExternalStore,
  type ReactNode,
} from "react";
import { readPreference, subscribeToPreferences } from "@/lib/browser-preference";
import {
  appearanceStorageKey,
  defaultAppearance,
  resolveAppearance,
  syncThemeColorMeta,
  type Appearance,
} from "./appearance";

const AppearanceContext = createContext<Appearance>(defaultAppearance);

export function AppearanceProvider({
  appearance,
  children,
}: {
  appearance: Appearance;
  children: ReactNode;
}) {
  const saved = useSyncExternalStore(
    subscribeToPreferences,
    () => resolveAppearance(readPreference(appearanceStorageKey)),
    () => appearance,
  );

  useLayoutEffect(() => {
    const root =
      typeof document !== "undefined" ? document.documentElement : null;
    if (root?.dataset) {
      root.dataset.appearance = saved;
    }
    syncThemeColorMeta(saved);
  }, [saved]);

  return <AppearanceContext value={saved}>{children}</AppearanceContext>;
}

export function useAppearance(): Appearance {
  return useContext(AppearanceContext);
}

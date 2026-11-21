"use client";

import {
  createContext,
  useContext,
  useLayoutEffect,
  useMemo,
  useSyncExternalStore,
  type ReactNode,
} from "react";
import { readPreference, subscribeToPreferences } from "@/lib/browser-preference";
import {
  defaultLocale,
  localeStorageKey,
  resolveLocale,
  type Locale,
} from "./locale";
import { createTranslator, type Translator } from "./translate";

const LocaleContext = createContext<Locale>(defaultLocale);

export function LocaleProvider({
  locale,
  children,
}: {
  locale: Locale;
  children: ReactNode;
}) {
  const saved = useSyncExternalStore(
    subscribeToPreferences,
    () => resolveLocale(readPreference(localeStorageKey)),
    () => locale,
  );

  useLayoutEffect(() => {
    const root =
      typeof document !== "undefined" ? document.documentElement : null;
    if (!root) return;
    root.lang = saved;
    if (
      root.dataset &&
      saved === resolveLocale(readPreference(localeStorageKey))
    ) {
      delete root.dataset.localePending;
    }
  }, [saved]);

  return <LocaleContext value={saved}>{children}</LocaleContext>;
}

export function useLocale(): Locale {
  return useContext(LocaleContext);
}

export function useTranslations(): Translator {
  const locale = useLocale();
  return useMemo(() => createTranslator(locale), [locale]);
}

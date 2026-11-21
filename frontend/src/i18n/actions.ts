"use client";

import { savePreference } from "@/lib/browser-preference";
import { isLocale, localeStorageKey } from "./locale";

export async function saveLocale(locale: unknown): Promise<void> {
  if (!isLocale(locale)) {
    throw new Error("Unsupported locale");
  }
  savePreference(localeStorageKey, locale);
}

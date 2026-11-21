"use client";

import { savePreference } from "@/lib/browser-preference";
import { appearanceStorageKey, isAppearance } from "./appearance";

export async function saveAppearance(appearance: unknown): Promise<void> {
  if (!isAppearance(appearance)) {
    throw new Error("Unsupported appearance");
  }
  savePreference(appearanceStorageKey, appearance);
}

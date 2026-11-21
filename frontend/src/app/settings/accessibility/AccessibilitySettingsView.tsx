"use client";

import Link from "next/link";
import { AccessibilityPreferencesControls } from "@/components/accessibility/AccessibilityPreferencesControls";
import { useTranslations } from "@/i18n/provider";

export function AccessibilitySettingsView() {
  const t = useTranslations();

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-3xl font-bold tracking-tight text-[var(--color-text)]">
          {t("Accessibility settings")}
        </h1>
        <Link
          href="/"
          className="inline-flex min-h-11 items-center rounded-md border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2 text-sm font-semibold text-[var(--color-accent-text)] hover:border-[var(--color-accent)]"
        >
          {t("Back to home")}
        </Link>
      </div>

      <div className="rounded-lg border-2 border-[var(--color-border)] bg-[var(--color-surface)] p-6">
        <AccessibilityPreferencesControls layout="settings" />
      </div>
    </div>
  );
}

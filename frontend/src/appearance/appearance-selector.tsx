"use client";

import { useId } from "react";
import { useAccessibilityPreferences } from "@/components/accessibility/AccessibilityProvider";
import { useTranslations } from "@/i18n/provider";
import { isAppearance } from "./appearance";

export type AppearanceSelectorProps = {
  hideLabel?: boolean;
  className?: string;
};

export function AppearanceSelector({
  hideLabel = false,
  className,
}: AppearanceSelectorProps = {}) {
  const { appearance, setAppearance } = useAccessibilityPreferences();
  const t = useTranslations();
  const selectId = useId();

  return (
    <div className={["inline-flex flex-col gap-1", className].filter(Boolean).join(" ")}>
      <div className="inline-flex items-center gap-2">
        <label
          htmlFor={selectId}
          className={
            hideLabel
              ? "sr-only"
              : "text-sm font-medium text-[var(--color-text-muted)]"
          }
        >
          {t("Appearance")}
        </label>
        <select
          id={selectId}
          value={appearance}
          onChange={(event) => {
            const value = event.target.value;
            if (!isAppearance(value) || value === appearance) return;
            setAppearance(value);
          }}
          className="min-h-11 cursor-pointer rounded-md border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm font-medium text-[var(--color-text)] transition-colors hover:border-[var(--color-accent)]"
        >
          <option value="system">{t("System")}</option>
          <option value="light">{t("Light")}</option>
          <option value="dark">{t("Dark")}</option>
          <option value="hc-black-white">{t("High contrast: Black & White")}</option>
          <option value="hc-black-yellow">{t("High contrast: Black & Yellow")}</option>
          <option value="grayscale">{t("Grayscale")}</option>
        </select>
      </div>
    </div>
  );
}

"use client";

import { useTranslations } from "@/i18n/provider";

/** Always-visible 112 call-to-action (DEC-008 / DEC-010). */
export function EmergencyBanner() {
  const t = useTranslations();

  return (
    <aside
      aria-label={t("Emergency number")}
      className="flex flex-col gap-3 rounded-xl border-2 border-[var(--color-error-border)] bg-[var(--color-error-badge)] p-4 text-[var(--color-error-on-badge)] sm:flex-row sm:items-center sm:justify-between sm:gap-6 sm:px-6"
    >
      <p className="text-lg leading-snug sm:text-xl">
        <span aria-hidden="true">☎ </span>
        <strong className="font-extrabold uppercase">{t("Cardiac arrest?")}</strong>{" "}
        {t("Call 112, start CPR and send someone for the AED.")}
      </p>
      <a
        href="tel:112"
        className="inline-flex min-h-14 shrink-0 items-center justify-center rounded-lg border-2 border-[var(--color-error-on-badge)] bg-[var(--color-error-on-badge)] px-6 text-xl font-extrabold tracking-wide text-[var(--color-error-badge)] no-underline sm:min-w-56"
      >
        {t("Call 112")}
      </a>
    </aside>
  );
}

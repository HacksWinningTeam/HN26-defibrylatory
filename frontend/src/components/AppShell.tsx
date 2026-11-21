"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { AppearanceSelector } from "@/appearance/appearance-selector";
import { AccessibilityMenu } from "@/components/accessibility/AccessibilityMenu";
import { LanguageSelector } from "@/i18n/language-selector";
import { useTranslations } from "@/i18n/provider";

export function AppShell({ children }: { children: ReactNode }) {
  const t = useTranslations();

  return (
    <>
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:inline-flex focus:min-h-11 focus:items-center focus:rounded-md focus:bg-[var(--color-accent)] focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-[var(--color-on-accent)] focus:shadow-md"
      >
        {t("Skip to main content")}
      </a>

      <header className="border-b border-[var(--color-border-subtle)] bg-[var(--color-surface)]">
        <div className="mx-auto flex w-full max-w-7xl flex-wrap items-center justify-between gap-4 px-4 py-3 sm:px-6">
          <Link href="/" className="flex min-h-11 items-center gap-3 text-[var(--color-text)] no-underline">
            <span aria-hidden="true" className="aed-pin h-10 w-10 shrink-0">
              <svg viewBox="0 0 24 24" focusable="false">
                <path fill="#fff" d="M12 21.6 3.4 13.2A5.4 5.4 0 0 1 12 6.4a5.4 5.4 0 0 1 8.6 6.8Z" />
                <path fill="#00703c" d="M12.9 8.4 9.6 13.3h2.3l-.9 4.3 3.4-5.2h-2.4Z" />
              </svg>
            </span>
            <span className="flex flex-col">
              <span className="text-lg leading-tight font-extrabold tracking-tight">{t("Misja AED")}</span>
              <span className="text-sm font-medium text-[var(--color-text-muted)]">
                {t("Data that saves lives")}
              </span>
            </span>
          </Link>
          <div className="flex flex-wrap items-center gap-3">
            <LanguageSelector />
            <AppearanceSelector />
          </div>
        </div>
      </header>

      <main id="main-content" tabIndex={-1} className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 sm:px-6">
        {children}
      </main>

      <footer className="border-t border-[var(--color-border-subtle)] bg-[var(--color-surface)]">
        <div className="mx-auto flex w-full max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-4 pr-20 text-sm text-[var(--color-text-muted)] sm:px-6 sm:pr-20">
          <span>
            {t("Map data © OpenStreetMap contributors (ODbL)")} &middot; HackNation 2026
          </span>
          <Link
            href="/settings/accessibility"
            className="inline-flex min-h-11 items-center font-semibold text-[var(--color-accent-text)] underline decoration-2 underline-offset-2"
          >
            {t("Accessibility settings")}
          </Link>
        </div>
      </footer>

      <AccessibilityMenu />
    </>
  );
}

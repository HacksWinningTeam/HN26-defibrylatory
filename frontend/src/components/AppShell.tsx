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
        <div className="mx-auto flex w-full max-w-4xl flex-wrap items-center justify-between gap-4 px-6 py-4">
          <div className="flex flex-col">
            <p className="text-base font-bold tracking-tight text-[var(--color-text)]">
              {t("Django + DRF + Next.js")}
            </p>
            <p className="text-sm font-medium text-[var(--color-text-muted)]">
              {t("Docker Full-Stack Template")}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <LanguageSelector />
            <AppearanceSelector />
          </div>
        </div>
      </header>

      <main id="main-content" className="mx-auto w-full max-w-4xl flex-1 px-6 py-10">
        {children}
      </main>

      <footer className="border-t border-[var(--color-border-subtle)] bg-[var(--color-surface)]">
        <div className="mx-auto flex w-full max-w-4xl flex-wrap items-center justify-between gap-3 px-6 py-4 text-sm text-[var(--color-text-muted)]">
          <span>
            Django 5.2 LTS &middot; Django REST Framework &middot; drf-spectacular &middot;
            PostgreSQL 18 &middot; Next.js 16
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

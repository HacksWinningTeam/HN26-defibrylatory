"use client";

import { HealthStatusCard } from "@/components/HealthStatusCard";
import { useTranslations } from "@/i18n/provider";
import type { HealthCheckResult } from "@/lib/api";

interface HomeViewProps {
  initialHealth: HealthCheckResult;
  publicApiUrl: string;
}

export function HomeView({ initialHealth, publicApiUrl }: Readonly<HomeViewProps>) {
  const t = useTranslations();

  const quickLinks = [
    {
      label: t("Swagger UI"),
      description: t("Interactive OpenAPI 3 documentation"),
      href: `${publicApiUrl}/api/docs/`,
    },
    {
      label: t("ReDoc"),
      description: t("Clean API reference powered by drf-spectacular"),
      href: `${publicApiUrl}/api/redoc/`,
    },
    {
      label: t("OpenAPI Schema"),
      description: t("Raw OpenAPI 3 specification"),
      href: `${publicApiUrl}/api/schema/`,
    },
    {
      label: t("Django Admin"),
      description: t("Built-in administrative console"),
      href: `${publicApiUrl}/admin/`,
    },
  ];

  return (
    <div className="space-y-8">
      <section aria-labelledby="intro-heading" className="space-y-3">
        <h1
          id="intro-heading"
          className="text-3xl font-bold tracking-tight text-[var(--color-text)] sm:text-4xl"
        >
          {t("Full-Stack Docker Template Ready")}
        </h1>
        <p className="max-w-2xl text-base leading-relaxed text-[var(--color-text-muted)]">
          {t(
            "This starter pairs a Django 5.2 LTS and Django REST Framework backend with a Next.js 16 App Router frontend and PostgreSQL 18, wired together for both local hot-reload development and production builds.",
          )}
        </p>
      </section>

      <HealthStatusCard
        initialResult={initialHealth}
        publicApiUrl={publicApiUrl}
      />

      <section aria-labelledby="links-heading" className="space-y-4">
        <h2
          id="links-heading"
          className="text-xl font-bold text-[var(--color-text)]"
        >
          {t("API Documentation & Admin Links")}
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {quickLinks.map((item) => (
            <a
              key={item.href}
              href={item.href}
              target="_blank"
              rel="noopener noreferrer"
              className="flex min-h-11 flex-col justify-between rounded-lg border-2 border-[var(--color-border)] bg-[var(--color-surface)] p-4 transition-colors hover:border-[var(--color-accent)] hover:bg-[var(--color-surface-raised)]"
            >
              <span className="text-base font-bold text-[var(--color-accent-text)] underline decoration-2 underline-offset-2">
                {item.label}
              </span>
              <span className="mt-1 text-sm text-[var(--color-text-muted)]">
                {item.description}
              </span>
            </a>
          ))}
        </div>
      </section>
    </div>
  );
}

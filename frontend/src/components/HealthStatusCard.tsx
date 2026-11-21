"use client";

import { useState } from "react";
import { useTranslations } from "@/i18n/provider";
import { fetchHealth, type HealthCheckResult } from "@/lib/api";

interface HealthStatusCardProps {
  initialResult: HealthCheckResult;
  publicApiUrl: string;
}

export function HealthStatusCard({
  initialResult,
  publicApiUrl,
}: Readonly<HealthStatusCardProps>) {
  const t = useTranslations();
  const [result, setResult] = useState<HealthCheckResult>(initialResult);
  const [source, setSource] = useState<"server" | "browser">("server");
  const [isChecking, setIsChecking] = useState(false);

  async function handleRecheck() {
    setIsChecking(true);
    const nextResult = await fetchHealth();
    setResult(nextResult);
    setSource("browser");
    setIsChecking(false);
  }

  const isHealthy = result.ok;
  const apiLabel = isHealthy
    ? t("Healthy")
    : result.data
      ? t("Degraded")
      : t("Unreachable");
  const dbLabel =
    result.data?.database === "ok"
      ? t("Connected")
      : result.data?.database === "error"
        ? t("Error")
        : t("Unknown");

  return (
    <section
      aria-labelledby="health-heading"
      className="rounded-lg border-2 border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-xs"
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2
            id="health-heading"
            className="text-xl font-bold text-[var(--color-text)]"
          >
            {t("Backend & Database Connectivity")}
          </h2>
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">
            {t("Verified via")}{" "}
            <code className="rounded bg-[var(--color-surface-raised)] px-1.5 py-0.5 font-mono text-xs text-[var(--color-text)]">
              {publicApiUrl}/api/health/
            </code>
          </p>
        </div>

        <button
          type="button"
          onClick={handleRecheck}
          disabled={isChecking}
          aria-busy={isChecking}
          className="inline-flex min-h-11 cursor-pointer items-center justify-center rounded-md bg-[var(--color-accent)] px-4 py-2 text-sm font-semibold text-[var(--color-on-accent)] transition-colors hover:bg-[var(--color-accent-hover)] disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isChecking ? t("Checking API...") : t("Re-check API")}
        </button>
      </div>

      <div
        role="status"
        aria-live="polite"
        className={`mt-5 rounded-md border-2 p-4 ${
          isHealthy
            ? "border-[var(--color-success-border)] bg-[var(--color-success-bg)] text-[var(--color-success-text)]"
            : "border-[var(--color-error-border)] bg-[var(--color-error-bg)] text-[var(--color-error-text)]"
        }`}
      >
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="text-base font-bold">
            <span
              className={`mr-2 inline-block rounded px-2 py-0.5 font-mono text-xs font-bold uppercase ${
                isHealthy
                  ? "bg-[var(--color-success-badge)] text-[var(--color-success-on-badge)]"
                  : "bg-[var(--color-error-badge)] text-[var(--color-error-on-badge)]"
              }`}
            >
              {isHealthy ? t("PASS") : t("FAIL")}
            </span>
            {t("API Status: {0}", { 0: apiLabel })}
          </p>
          <span className="text-xs font-semibold uppercase tracking-wide">
            {t("Source:")}{" "}
            {source === "server"
              ? t("Server SSR")
              : publicApiUrl
                ? t("Browser Fetch (CORS)")
                : t("Browser Fetch (Same-Origin Proxy)")}
          </span>
        </div>

        <dl className="mt-4 grid grid-cols-1 gap-3 text-sm sm:grid-cols-3">
          <div>
            <dt className="font-semibold">{t("HTTP Status")}</dt>
            <dd className="mt-0.5 font-mono">
              {result.statusCode !== null
                ? result.statusCode
                : t("No response")}
            </dd>
          </div>
          <div>
            <dt className="font-semibold">{t("PostgreSQL Database")}</dt>
            <dd className="mt-0.5 font-mono">{dbLabel}</dd>
          </div>
          <div>
            <dt className="font-semibold">{t("Server Timestamp (UTC)")}</dt>
            <dd className="mt-0.5 font-mono break-all">
              {result.data?.timestamp ?? t("N/A")}
            </dd>
          </div>
        </dl>

        {result.error ? (
          <p className="mt-3 border-t border-[var(--color-error-border)] pt-3 text-sm font-medium">
            {t("Detail: {0}", { 0: result.error })}
          </p>
        ) : null}
      </div>
    </section>
  );
}

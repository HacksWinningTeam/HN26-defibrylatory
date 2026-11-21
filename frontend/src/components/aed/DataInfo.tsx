"use client";

import { useLocale, useTranslations } from "@/i18n/provider";
import type { SourcesReport } from "@/lib/api";
import { ExternalLink } from "./AedDetails";

const linkClass =
  "inline-flex min-h-11 items-center rounded-lg border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-4 font-semibold text-[var(--color-accent-text)] no-underline hover:bg-[var(--color-surface-raised)]";

/** "Skąd są te dane?" — counts, harvested sources and download / API links. */
export function DataInfo({
  report,
  forkUrl,
}: {
  report: SourcesReport | null;
  forkUrl: string | null;
}) {
  const t = useTranslations();
  const locale = useLocale();
  const number = new Intl.NumberFormat(locale);
  const updated = report?.updated_at
    ? new Intl.DateTimeFormat(locale, { dateStyle: "long", timeZone: "Europe/Warsaw" }).format(new Date(report.updated_at))
    : "—";

  return (
    <section
      id="data-info"
      tabIndex={-1}
      aria-labelledby="data-info-heading"
      className="flex flex-col gap-4 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5"
    >
      <h2 id="data-info-heading" className="text-2xl font-bold">
        {t("Where does this data come from?")}
      </h2>
      <p className="max-w-3xl text-base">
        {t(
          "One national dataset built automatically from all AED datasets on dane.gov.pl and OpenStreetMap, mapped to one standard schema and deduplicated.",
        )}
      </p>

      {report ? (
        <>
          <p className="text-lg font-semibold">
            {t("{0} AEDs from {1} sources, updated {2}.", {
              0: number.format(report.aed_count),
              1: number.format(report.sources.length),
              2: updated,
            })}
          </p>
          <div>
            <h3 className="mb-2 text-lg font-bold">{t("Sources")}</h3>
            <ul className="flex flex-col gap-1" role="list">
              {report.sources.map((source) => (
                <li key={source.id} className="text-base">
                  {source.url ? <ExternalLink href={source.url}>{source.title}</ExternalLink> : source.title}{" "}
                  <span className="text-[var(--color-text-muted)]">
                    — {t("{0} records", { 0: number.format(source.record_count) })}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </>
      ) : (
        <p role="status" className="text-[var(--color-text-muted)]">
          {t("Source statistics are unavailable right now.")}
        </p>
      )}

      <div className="flex flex-col gap-2">
        <h3 className="text-lg font-bold">{t("Downloads and API")}</h3>
        <ul className="flex flex-wrap gap-2" role="list">
          <li>
            <a href="/api/schema-standard/aed-schema.xlsx" className={linkClass}>
              {t("Standard AED schema")} (XLSX)
            </a>
          </li>
          <li>
            <a href="/api/schema-standard/aed-schema.csv" className={linkClass}>
              {t("Standard AED schema")} (CSV)
            </a>
          </li>
          <li>
            <a href="/api/schema-standard/aed-schema.json" className={linkClass}>
              JSON Schema
            </a>
          </li>
          <li>
            <a href="/api/exports/aed.csv" className={linkClass}>
              {t("Download the dataset")} (CSV)
            </a>
          </li>
          <li>
            <a href="/api/exports/aed.geojson" className={linkClass}>
              {t("Download the dataset")} (GeoJSON)
            </a>
          </li>
          <li>
            <a href="/api/exports/aed.xlsx" className={linkClass}>
              {t("Download the dataset")} (XLSX)
            </a>
          </li>
          <li>
            <a href="/api/1.4/datasets/1" className={linkClass}>
              {t("dane.gov.pl-compatible API")}
            </a>
          </li>
          <li>
            <a href="/api/docs/" className={linkClass}>
              {t("API documentation")}
            </a>
          </li>
          {forkUrl && (
            <li>
              <ExternalLink href={forkUrl} className={linkClass}>
                {t("Dataset on dane.gov.pl (fork)")}
              </ExternalLink>
            </li>
          )}
        </ul>
      </div>

      <p className="text-sm text-[var(--color-text-muted)]">
        {t("Licence: ODbL 1.0 (contains OpenStreetMap data)")}
      </p>
    </section>
  );
}

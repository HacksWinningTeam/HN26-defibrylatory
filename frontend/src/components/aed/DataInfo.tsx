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
  portalApiUrl = null,
}: {
  report: SourcesReport | null;
  forkUrl: string | null;
  /** Public dane.gov.pl fork API (T15); null = links to our old backend. */
  portalApiUrl?: string | null;
}) {
  const t = useTranslations();
  const locale = useLocale();
  const number = new Intl.NumberFormat(locale);
  const updated = report?.updated_at
    ? new Intl.DateTimeFormat(locale, { dateStyle: "long", timeZone: "Europe/Warsaw" }).format(new Date(report.updated_at))
    : "—";

  const schema = t("Standard AED schema");
  const download = t("Download the dataset");
  const links: { href: string; label: string; external: boolean }[] = portalApiUrl
    ? [
        { href: `${portalApiUrl}/1.4/aed/schema.xlsx`, label: `${schema} (XLSX)`, external: true },
        { href: `${portalApiUrl}/1.4/aed/schema.csv`, label: `${schema} (CSV)`, external: true },
        { href: `${portalApiUrl}/1.4/aed/schema.json`, label: "JSON Schema", external: true },
        ...(forkUrl ? [{ href: forkUrl, label: t("Dataset on dane.gov.pl (fork)"), external: true }] : []),
        { href: `${portalApiUrl}/1.4/aed/devices`, label: `${download} (GeoJSON, API)`, external: true },
        { href: `${portalApiUrl}/1.4/aed/sources`, label: t("dane.gov.pl-compatible API"), external: true },
        { href: `${portalApiUrl}/1.4/aed/validate`, label: t("Data validation API"), external: true },
      ]
    : [
        { href: "/api/schema-standard/aed-schema.xlsx", label: `${schema} (XLSX)`, external: false },
        { href: "/api/schema-standard/aed-template.csv", label: `${schema} (CSV)`, external: false },
        { href: "/api/schema-standard/aed-schema.json", label: "JSON Schema", external: false },
        { href: "/api/exports/aed.csv", label: `${download} (CSV)`, external: false },
        { href: "/api/exports/aed.geojson", label: `${download} (GeoJSON)`, external: false },
        { href: "/api/exports/aed.xlsx", label: `${download} (XLSX)`, external: false },
        { href: "/api/1.4/datasets/1", label: t("dane.gov.pl-compatible API"), external: false },
        { href: "/api/docs/", label: t("API documentation"), external: false },
        ...(forkUrl ? [{ href: forkUrl, label: t("Dataset on dane.gov.pl (fork)"), external: true }] : []),
      ];

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
          {links.map((link) => (
            <li key={link.href}>
              {link.external ? (
                <ExternalLink href={link.href} className={linkClass}>
                  {link.label}
                </ExternalLink>
              ) : (
                <a href={link.href} className={linkClass}>
                  {link.label}
                </a>
              )}
            </li>
          ))}
        </ul>
      </div>

      <p className="text-sm text-[var(--color-text-muted)]">
        {t("Licence: ODbL 1.0 (contains OpenStreetMap data)")}
      </p>
    </section>
  );
}

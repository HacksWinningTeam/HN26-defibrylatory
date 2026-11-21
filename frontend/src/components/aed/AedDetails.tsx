"use client";

import type { ReactNode } from "react";
import { useTranslations } from "@/i18n/provider";
import { BADGE_VARIANTS, topBadges, type AedProperties } from "@/lib/aed";
import { Badge } from "@/components/ui/Badge";
import {
  type PlainMessageKey,
  BADGE_LABELS,
  DOSTEP_LABELS,
  STATUS_LABELS,
  ZABEZPIECZENIE_LABELS,
} from "./labels";

const linkClass =
  "font-semibold text-[var(--color-accent-text)] underline decoration-2 underline-offset-2";

export function ExternalLink({
  href,
  children,
  className = linkClass,
}: {
  href: string;
  children: ReactNode;
  className?: string;
}) {
  const t = useTranslations();
  return (
    <a href={href} target="_blank" rel="noopener noreferrer" className={className}>
      {children}
      <span aria-hidden="true"> ↗</span>
      <span className="sr-only"> {t("(opens in a new tab)")}</span>
    </a>
  );
}

export function AedBadges({ props }: { props: AedProperties }) {
  const t = useTranslations();
  return (
    <ul className="flex flex-wrap gap-2" role="list">
      {topBadges(props).map((kind) => (
        <li key={kind}>
          <Badge variant={BADGE_VARIANTS[kind]} icon={BADGE_LABELS[kind].icon}>
            {t(BADGE_LABELS[kind].label)}
          </Badge>
        </li>
      ))}
    </ul>
  );
}

/** Key/value details of one AED; rows with no data are hidden (DEC-010). */
export function AedDetails({ props }: { props: AedProperties }) {
  const t = useTranslations();

  const enumLabel = (labels: Record<string, PlainMessageKey>, code: string | null) =>
    code ? (labels[code] ? t(labels[code]) : code) : null;

  const where = [
    props.opis_lokalizacji,
    props.pietro !== null && props.pietro !== ""
      ? t("Floor {0}", { 0: String(props.pietro) })
      : null,
    props.w_budynku === true ? t("Indoors") : props.w_budynku === false ? t("Outdoors") : null,
  ]
    .filter(Boolean)
    .join(" · ");

  const rows: { key: string; label: string; value: ReactNode }[] = [];
  const add = (key: string, label: string, value: ReactNode) => {
    if (value !== null && value !== undefined && value !== "") rows.push({ key, label, value });
  };

  add("adres", t("Address"), props.adres ?? props.miejscowosc);
  add("where", t("Exact location"), where || null);
  add("hours", t("Opening hours"), props.godziny_dostepnosci);
  add("access", t("Access"), enumLabel(DOSTEP_LABELS, props.dostep));
  add("security", t("Security"), enumLabel(ZABEZPIECZENIE_LABELS, props.zabezpieczenie));
  add("status", t("Status"), enumLabel(STATUS_LABELS, props.status));
  add("operator", t("Operator"), props.dysponent);
  add(
    "phone",
    t("Phone"),
    props.telefon_kontaktowy ? (
      <a href={`tel:${props.telefon_kontaktowy.replace(/[^\d+]/g, "")}`} className={linkClass}>
        {props.telefon_kontaktowy}
      </a>
    ) : null,
  );
  add(
    "sources",
    t("Sources"),
    props.zrodla.length > 0 ? (
      <ul className="flex flex-col gap-1" role="list">
        {props.zrodla.map((source, index) => (
          <li key={`${source.url ?? source.nazwa}-${index}`}>
            {source.url ? <ExternalLink href={source.url}>{source.nazwa}</ExternalLink> : source.nazwa}
          </li>
        ))}
      </ul>
    ) : null,
  );
  add("updated", t("Updated"), props.data_aktualizacji);

  return (
    <dl className="grid grid-cols-1 gap-x-4 gap-y-2 text-base sm:grid-cols-[minmax(8rem,auto)_1fr]">
      {rows.map((row) => (
        <div key={row.key} className="contents">
          <dt className="font-semibold text-[var(--color-text-muted)]">{row.label}</dt>
          <dd className="mb-1 break-words sm:mb-0">{row.value}</dd>
        </div>
      ))}
    </dl>
  );
}

"use client";

import { useLocale, useTranslations } from "@/i18n/provider";
import {
  FAR_AWAY_M,
  aedTitle,
  featureLatLon,
  formatDistance,
  osmDirectionsUrl,
  walkingMinutes,
  type LatLon,
  type NearbyAed,
} from "@/lib/aed";
import { Badge } from "@/components/ui/Badge";
import { AedBadges, AedDetails, ExternalLink } from "./AedDetails";

export const primaryButtonClass =
  "inline-flex min-h-14 w-full items-center justify-center gap-2 rounded-lg bg-[var(--color-accent)] px-6 text-xl font-extrabold uppercase tracking-wide text-[var(--color-on-accent)] no-underline hover:bg-[var(--color-accent-hover)]";

/** The #1 AED: huge distance, title, ≤ 3 badges, "PROWADŹ DO AED" (DEC-010). */
export function NearestCard({
  aed,
  from,
  selected,
  onShowOnMap,
}: {
  aed: NearbyAed;
  from: LatLon;
  selected: boolean;
  onShowOnMap: (id: string) => void;
}) {
  const t = useTranslations();
  const locale = useLocale();
  const props = aed.feature.properties;
  const title = aedTitle(props) ?? t("AED defibrillator");
  const description = props.opis_lokalizacji?.trim();
  const showDescription = Boolean(description) && !title.includes(description ?? "");

  return (
    <article
      aria-labelledby="nearest-aed-title"
      className={`flex flex-col gap-4 rounded-xl bg-[var(--color-surface)] p-5 shadow-sm ${
        selected
          ? "border-4 border-[var(--color-accent)]"
          : "border-2 border-[var(--color-border)]"
      }`}
    >
      <div>
        <p className="text-5xl leading-none font-extrabold tracking-tight">
          {formatDistance(aed.distanceM, locale)}
        </p>
        <p className="mt-2 text-base text-[var(--color-text-muted)]">
          {t("about {0} min on foot", { 0: walkingMinutes(aed.distanceM) })} ·{" "}
          {t("straight-line distance")}
        </p>
      </div>

      <div className="flex flex-col gap-1">
        <h2 id="nearest-aed-title" className="text-xl leading-snug font-bold">
          <span className="sr-only">{t("AED no. {0}", { 0: 1 })}: </span>
          {title}
        </h2>
        {(props.adres || props.miejscowosc) && (
          <p className="text-base">{props.adres ?? props.miejscowosc}</p>
        )}
        {showDescription && (
          <p className="text-base text-[var(--color-text-muted)]">{props.opis_lokalizacji}</p>
        )}
      </div>

      <AedBadges props={props} />

      {aed.distanceM > FAR_AWAY_M && (
        <Badge variant="warning" icon="☎">
          {t("Far away – call 112, the dispatcher will point you to the nearest AED")}
        </Badge>
      )}

      <ExternalLink
        href={osmDirectionsUrl(from, featureLatLon(aed.feature))}
        className={primaryButtonClass}
      >
        <span aria-hidden="true">➜</span> {t("Navigate to AED")}
      </ExternalLink>

      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={() => onShowOnMap(aed.feature.id)}
          aria-pressed={selected}
          className="inline-flex min-h-11 items-center rounded-lg border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-4 font-semibold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)]"
        >
          <span aria-hidden="true">🗺&nbsp;</span>
          {t("Show on map")}
          {selected && <span className="ml-2 text-sm">({t("Selected")})</span>}
        </button>
      </div>

      <details className="group rounded-lg border border-[var(--color-border-subtle)] p-3">
        <summary className="flex min-h-11 cursor-pointer items-center font-semibold text-[var(--color-accent-text)]">
          {t("More information")}
        </summary>
        <div className="pt-3">
          <AedDetails props={props} />
        </div>
      </details>
    </article>
  );
}

"use client";

import { useLocale, useTranslations } from "@/i18n/provider";
import {
  aedTitle,
  featureLatLon,
  formatDistance,
  osmDirectionsUrl,
  type LatLon,
  type NearbyAed,
} from "@/lib/aed";
import { AedBadges, ExternalLink } from "./AedDetails";

/** AEDs #2..#5 as compact rows; numbers match the map pins. */
export function NearbyList({
  items,
  from,
  selectedId,
  onShowOnMap,
}: {
  items: NearbyAed[];
  from: LatLon;
  selectedId: string | null;
  onShowOnMap: (id: string) => void;
}) {
  const t = useTranslations();
  const locale = useLocale();
  if (items.length === 0) return null;

  return (
    <section aria-labelledby="nearby-heading" className="flex flex-col gap-3">
      <h2 id="nearby-heading" className="text-xl font-bold">
        {t("Other AEDs nearby")}
      </h2>
      <ol className="flex flex-col gap-3" role="list">
        {items.map((item) => {
          const props = item.feature.properties;
          const selected = selectedId === item.feature.id;
          return (
            <li
              key={item.feature.id}
              className={`flex flex-col gap-2 rounded-lg bg-[var(--color-surface)] p-3 ${
                selected
                  ? "border-4 border-[var(--color-accent)]"
                  : "border border-[var(--color-border)]"
              }`}
            >
              <div className="flex items-start gap-3">
                <span
                  aria-hidden="true"
                  className="aed-pin aed-pin--ranked mt-0.5 h-10 w-10 shrink-0"
                >
                  {item.rank}
                </span>
                <div className="min-w-0 flex-1">
                  <h3 className="text-base leading-snug font-bold">
                    <span className="sr-only">{t("AED no. {0}", { 0: item.rank })}: </span>
                    <span className="mr-2 whitespace-nowrap">
                      {formatDistance(item.distanceM, locale)}
                    </span>
                    · {aedTitle(props) ?? t("AED defibrillator")}
                  </h3>
                  {(props.adres || props.miejscowosc) && (
                    <p className="text-sm text-[var(--color-text-muted)]">
                      {props.adres ?? props.miejscowosc}
                    </p>
                  )}
                </div>
              </div>
              <AedBadges props={props} />
              <div className="flex flex-wrap gap-2">
                <ExternalLink
                  href={osmDirectionsUrl(from, featureLatLon(item.feature))}
                  className="inline-flex min-h-11 items-center rounded-lg bg-[var(--color-accent)] px-4 font-bold text-[var(--color-on-accent)] no-underline hover:bg-[var(--color-accent-hover)]"
                >
                  <span aria-hidden="true">➜&nbsp;</span>
                  {t("Navigate")}
                </ExternalLink>
                <button
                  type="button"
                  onClick={() => onShowOnMap(item.feature.id)}
                  aria-pressed={selected}
                  className="inline-flex min-h-11 items-center rounded-lg border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-4 font-semibold hover:bg-[var(--color-surface-raised)]"
                >
                  {t("Show on map")}
                  {selected && <span className="ml-2 text-sm">({t("Selected")})</span>}
                </button>
              </div>
            </li>
          );
        })}
      </ol>
    </section>
  );
}

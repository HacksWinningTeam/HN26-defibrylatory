"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useLocale, useTranslations } from "@/i18n/provider";
import { fetchAeds } from "@/lib/api";
import {
  aedTitle,
  formatDistance,
  nearestAeds,
  type AedFeature,
  type UserLocation,
} from "@/lib/aed";
import { NearbyList } from "./NearbyList";
import { NearestCard } from "./NearestCard";

function MapLoading() {
  const t = useTranslations();
  return (
    <div className="flex h-full items-center justify-center bg-[var(--color-surface-raised)] text-[var(--color-text-muted)]">
      {t("Loading map…")}
    </div>
  );
}

const AedMap = dynamic(() => import("./AedMap"), { ssr: false, loading: () => <MapLoading /> });

type LoadState =
  | { status: "loading" }
  | { status: "ready"; features: AedFeature[] }
  | { status: "error" };

const NEAREST_COUNT = 5;

/** "Najbliższy AED" page body: location, #1 card, #2–#5 list, map (DEC-010). */
export function AedFinder({ location }: { location: UserLocation }) {
  const t = useTranslations();
  const locale = useLocale();
  const [state, setState] = useState<LoadState>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetchAeds(controller.signal)
      .then((data) => setState({ status: "ready", features: data.features ?? [] }))
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          console.error(error);
          setState({ status: "error" });
        }
      });
    return () => controller.abort();
  }, [attempt]);

  const retry = useCallback(() => {
    setState({ status: "loading" });
    setAttempt((value) => value + 1);
  }, []);

  const features = state.status === "ready" ? state.features : null;
  const nearest = useMemo(
    () => (features ? nearestAeds(features, location, NEAREST_COUNT) : []),
    [features, location],
  );
  const first = nearest[0];

  const announcement =
    state.status === "ready" && first
      ? t("Nearest AED: {0}, {1}", {
          0: formatDistance(first.distanceM, locale),
          1: aedTitle(first.feature.properties) ?? t("AED defibrillator"),
        })
      : "";

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-[28rem_minmax(0,1fr)] lg:items-start">
      <div className="flex flex-col gap-5 pb-20 lg:pb-0">
        <p className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-4 text-base">
          <span aria-hidden="true">📍 </span>
          <strong>{t("You are here:")}</strong> {location.label}
          {location.isDemo && (
            <span className="text-[var(--color-text-muted)]"> {t("(demo location)")}</span>
          )}
        </p>

        <h1 className="text-3xl font-extrabold tracking-tight uppercase">{t("Nearest AED")}</h1>

        <p aria-live="polite" className="sr-only">
          {announcement}
        </p>

        {state.status === "loading" && (
          <div
            role="status"
            aria-busy="true"
            className="flex flex-col gap-3 rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-surface)] p-5"
          >
            <span className="block h-12 w-32 animate-pulse rounded bg-[var(--color-surface-raised)]" />
            <span className="block h-6 w-3/4 animate-pulse rounded bg-[var(--color-surface-raised)]" />
            <span>{t("Looking for the nearest defibrillators…")}</span>
          </div>
        )}

        {state.status === "error" && (
          <div
            role="alert"
            className="flex flex-col items-start gap-3 rounded-xl border-2 border-[var(--color-error-border)] bg-[var(--color-error-bg)] p-5 text-[var(--color-error-text)]"
          >
            <p className="font-semibold">
              <span aria-hidden="true">⚠ </span>
              {t("Could not load defibrillators.")}
            </p>
            <button
              type="button"
              onClick={retry}
              className="inline-flex min-h-11 items-center rounded-lg bg-[var(--color-accent)] px-4 font-bold text-[var(--color-on-accent)] hover:bg-[var(--color-accent-hover)]"
            >
              {t("Try again")}
            </button>
          </div>
        )}

        {state.status === "ready" && !first && (
          <p className="rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-surface)] p-5 font-semibold">
            {t("The AED dataset has not been loaded yet.")}
          </p>
        )}

        {first && (
          <NearestCard
            aed={first}
            from={location}
            selected={selectedId === first.feature.id}
            onShowOnMap={setSelectedId}
          />
        )}

        <NearbyList
          items={nearest.slice(1)}
          from={location}
          selectedId={selectedId}
          onShowOnMap={setSelectedId}
        />
      </div>

      <section aria-labelledby="map-heading" className="flex flex-col gap-2 lg:sticky lg:top-4">
        <h2 id="map-heading" className="sr-only">
          {t("Map of defibrillators")}
        </h2>
        <a
          href="#data-info"
          className="sr-only focus:not-sr-only focus:inline-flex focus:min-h-11 focus:items-center focus:rounded-md focus:bg-[var(--color-accent)] focus:px-4 focus:font-semibold focus:text-[var(--color-on-accent)]"
        >
          {t("Skip the map")}
        </a>
        <div className="aed-map h-[60dvh] min-h-80 overflow-hidden rounded-xl border-2 border-[var(--color-border)] lg:h-[max(520px,calc(100dvh-14rem))]">
          <AedMap
            features={features}
            nearest={nearest}
            location={location}
            selectedId={selectedId}
            onSelect={setSelectedId}
          />
        </div>
      </section>
    </div>
  );
}

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

/** Width of the floating card on large screens + gap, kept free when the map fits the nearest AED. */
const CARD_SPACE_PX = 440;
const LARGE_SCREEN = "(min-width: 1024px)";

const call112Class =
  "inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border-2 border-[var(--color-error-badge)] bg-[var(--color-error-badge)] px-4 font-extrabold text-[var(--color-error-on-badge)] no-underline hover:opacity-90";

/** "/" (T21, DEC-021): full-height map, every AED clickable, one card for the nearest AED. */
export function MapFirstView({ location }: { location: UserLocation }) {
  const t = useTranslations();
  const locale = useLocale();
  const [state, setState] = useState<LoadState>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [largeScreen, setLargeScreen] = useState(false);

  useEffect(() => {
    const query = window.matchMedia(LARGE_SCREEN);
    const update = () => setLargeScreen(query.matches);
    update();
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);

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
    () => (features ? nearestAeds(features, location, 1) : []),
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
    <div className="relative flex flex-1 flex-col lg:min-h-[32rem]">
      <aside
        aria-labelledby="nearest-heading"
        className="order-2 flex flex-col gap-4 border-t-2 border-[var(--color-border)] bg-[var(--color-surface)] p-4 lg:absolute lg:top-4 lg:left-4 lg:z-[1100] lg:order-none lg:max-h-[calc(100%-2rem)] lg:w-[26rem] lg:overflow-y-auto lg:rounded-xl lg:border-2 lg:p-5 lg:shadow-lg"
      >
        <div className="flex items-center justify-between gap-3">
          <h1 id="nearest-heading" className="text-2xl font-extrabold tracking-tight uppercase">
            {t("Nearest AED")}
          </h1>
          <a href="tel:112" className={call112Class}>
            <span aria-hidden="true">📞</span> 112
            <span className="sr-only"> – {t("Call 112")}</span>
          </a>
        </div>

        <p aria-live="polite" className="sr-only">
          {announcement}
        </p>

        {state.status === "loading" && (
          <div role="status" aria-busy="true" className="flex flex-col gap-3">
            <span className="block h-12 w-32 animate-pulse rounded bg-[var(--color-surface-raised)]" />
            <span className="block h-6 w-3/4 animate-pulse rounded bg-[var(--color-surface-raised)]" />
            <span>{t("Looking for the nearest defibrillators…")}</span>
          </div>
        )}

        {state.status === "error" && (
          <div
            role="alert"
            className="flex flex-col items-start gap-3 rounded-lg border-2 border-[var(--color-error-border)] bg-[var(--color-error-bg)] p-4 text-[var(--color-error-text)]"
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
          <p className="font-semibold">{t("The AED dataset has not been loaded yet.")}</p>
        )}

        {first && (
          <NearestCard
            aed={first}
            from={location}
            selected={selectedId === first.feature.id}
            onShowOnMap={setSelectedId}
            compact
          />
        )}

        <p className="text-sm text-[var(--color-text-muted)]">
          <span aria-hidden="true">📍 </span>
          {t("You are here:")} {location.label}
          {location.isDemo && <> {t("(demo location)")}</>}
        </p>
      </aside>

      <section
        aria-labelledby="map-heading"
        className="aed-map relative order-1 h-[62dvh] min-h-80 lg:absolute lg:inset-0 lg:order-none lg:h-auto"
      >
        <h2 id="map-heading" className="sr-only">
          {t("Map of defibrillators")}
        </h2>
        <AedMap
          features={features}
          nearest={nearest}
          location={location}
          selectedId={selectedId}
          onSelect={setSelectedId}
          fitPaddingTopLeft={largeScreen ? [CARD_SPACE_PX, 48] : [48, 48]}
        />
      </section>
    </div>
  );
}

"use client";

// Client-only (loaded with next/dynamic { ssr: false } from MapFirstView).
import "leaflet/dist/leaflet.css";
import "leaflet.markercluster/dist/MarkerCluster.css";

import L from "leaflet";
import { useEffect, useRef } from "react";
import { useLocale, useTranslations } from "@/i18n/provider";
import type { Translator } from "@/i18n/translate";
import {
  aedTitle,
  featureLatLon,
  formatDistance,
  haversineMeters,
  osmDirectionsUrl,
  topBadges,
  type AedFeature,
  type NearbyAed,
  type UserLocation,
} from "@/lib/aed";
import { BADGE_LABELS } from "./labels";

/** White heart + lightning (ISO 7010 E010 convention), decorative. */
const AED_SVG =
  '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="#fff" d="M12 21.6 3.4 13.2A5.4 5.4 0 0 1 12 6.4a5.4 5.4 0 0 1 8.6 6.8Z"/><path fill="#00703c" d="M12.9 8.4 9.6 13.3h2.3l-.9 4.3 3.4-5.2h-2.4Z"/></svg>';

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (ch) => `&#${ch.charCodeAt(0)};`);
}

function prefersReducedMotion(): boolean {
  return typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

type LeafletWithCluster = typeof L & {
  markerClusterGroup: (options?: Record<string, unknown>) => L.FeatureGroup;
};

let clusterPluginPromise: Promise<LeafletWithCluster> | null = null;

/** leaflet.markercluster is a UMD plugin that augments the global `L`. */
function loadClusterPlugin(): Promise<LeafletWithCluster> {
  if (!clusterPluginPromise) {
    (window as unknown as { L: typeof L }).L = L;
    clusterPluginPromise = import("leaflet.markercluster").then(
      () => L as LeafletWithCluster,
    );
  }
  return clusterPluginPromise;
}

function el<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  className?: string,
  text?: string,
): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function externalLink(href: string, text: string, className: string, t: Translator) {
  const a = el("a", className, text);
  a.href = href;
  a.target = "_blank";
  a.rel = "noopener noreferrer";
  const arrow = el("span", "", " ↗");
  arrow.setAttribute("aria-hidden", "true");
  a.append(arrow, el("span", "sr-only", ` ${t("(opens in a new tab)")}`));
  return a;
}

/** Popup DOM built with textContent only (data comes from municipal files / OSM). */
function buildPopup(
  feature: AedFeature,
  rank: number | null,
  location: UserLocation,
  t: Translator,
  locale: string,
): HTMLElement {
  const props = feature.properties;
  const root = el("div", "flex flex-col gap-1.5 text-[var(--color-text)]");
  const heading = el("h3", "text-base font-bold leading-snug");
  heading.tabIndex = -1;
  heading.dataset.popupHeading = "true";
  heading.textContent = `${rank ? `${rank}. ` : ""}${aedTitle(props) ?? t("AED defibrillator")}`;
  root.append(heading);

  const distance = haversineMeters(location, featureLatLon(feature));
  root.append(
    el("p", "font-semibold", `${formatDistance(distance, locale)} · ${t("straight-line distance")}`),
  );
  const address = props.adres ?? props.miejscowosc;
  if (address) root.append(el("p", "", address));
  if (props.opis_lokalizacji && !heading.textContent.includes(props.opis_lokalizacji.trim())) {
    root.append(el("p", "text-[var(--color-text-muted)]", props.opis_lokalizacji));
  }
  const badges = topBadges(props)
    .map((kind) => `${BADGE_LABELS[kind].icon} ${t(BADGE_LABELS[kind].label)}`)
    .join(" · ");
  root.append(el("p", "font-semibold", badges));
  if (props.godziny_dostepnosci) {
    root.append(el("p", "", `${t("Opening hours")}: ${props.godziny_dostepnosci}`));
  }
  root.append(
    externalLink(
      osmDirectionsUrl(location, featureLatLon(feature)),
      `➜ ${t("Navigate")}`,
      "mt-1 inline-flex min-h-11 items-center justify-center rounded-lg bg-[var(--color-accent)] px-4 font-bold text-[var(--color-on-accent)]! no-underline",
      t,
    ),
  );
  if (props.zrodla.length > 0) {
    const sources = el("p", "text-sm", `${t("Sources")}: `);
    props.zrodla.forEach((source, index) => {
      if (index > 0) sources.append(", ");
      if (source.url) {
        sources.append(
          externalLink(source.url, source.nazwa, "text-[var(--color-accent-text)]! underline", t),
        );
      } else {
        sources.append(source.nazwa);
      }
    });
    root.append(sources);
  }
  return root;
}

function aedIcon(t: Translator, title: string): L.DivIcon {
  return L.divIcon({
    className: "",
    html: `<span class="aed-pin" style="width:44px;height:44px">${AED_SVG}<span class="sr-only">${escapeHtml(title)}</span></span>`,
    iconSize: [44, 44],
    iconAnchor: [22, 22],
    popupAnchor: [0, -20],
  });
}

function rankedIcon(rank: number, selected: boolean, t: Translator, title: string): L.DivIcon {
  const size = 52;
  return L.divIcon({
    className: "",
    html: `<span class="aed-pin aed-pin--ranked${selected ? " aed-pin--selected" : ""}" style="width:${size}px;height:${size}px"><span aria-hidden="true">${rank}</span><span class="sr-only">${escapeHtml(`${t("AED no. {0}", { 0: rank })}: ${title}${selected ? ` (${t("Selected")})` : ""}`)}</span></span>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -24],
  });
}

export interface AedMapProps {
  features: AedFeature[] | null;
  nearest: NearbyAed[];
  location: UserLocation;
  selectedId: string | null;
  onSelect: (id: string | null) => void;
  /** Extra space kept free on the top-left when fitting the nearest AED (e.g. under a floating card). */
  fitPaddingTopLeft?: [number, number];
}

export default function AedMap({
  features,
  nearest,
  location,
  selectedId,
  onSelect,
  fitPaddingTopLeft,
}: AedMapProps) {
  const t = useTranslations();
  const locale = useLocale();
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const rankedRef = useRef(new Map<string, { marker: L.Marker; rank: number; title: string }>());
  const onSelectRef = useRef(onSelect);
  const selectedRef = useRef(selectedId);
  const returnFocusRef = useRef<HTMLElement | null>(null);
  const fitPaddingRef = useRef(fitPaddingTopLeft);

  useEffect(() => {
    onSelectRef.current = onSelect;
    selectedRef.current = selectedId;
    fitPaddingRef.current = fitPaddingTopLeft;
  });

  // 1. Map, tiles, zoom control, "you are here" marker.
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const map = L.map(container, {
      zoomControl: false,
      keyboard: true,
      center: [location.lat, location.lon],
      zoom: 15,
      maxZoom: 19,
    });
    mapRef.current = map;
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a>',
    }).addTo(map);
    L.control
      .zoom({ position: "topright", zoomInTitle: t("Zoom in"), zoomOutTitle: t("Zoom out") })
      .addTo(map);
    L.marker([location.lat, location.lon], {
      interactive: false,
      keyboard: false,
      zIndexOffset: 1000,
      icon: L.divIcon({
        className: "",
        html: `<span class="aed-you"><span class="aed-you__dot"></span><span class="aed-you__label">${escapeHtml(t("You are here"))}</span></span>`,
        iconSize: [22, 22],
        iconAnchor: [11, 11],
      }),
    }).addTo(map);

    map.on("popupopen", (event: L.PopupEvent) => {
      const popupEl = event.popup.getElement();
      popupEl?.addEventListener("keydown", (keyEvent) => {
        if (keyEvent.key === "Escape") map.closePopup();
      });
      const closeButton = popupEl?.querySelector<HTMLAnchorElement>(".leaflet-popup-close-button");
      closeButton?.setAttribute("aria-label", t("Close"));
    });
    map.on("popupclose", () => {
      const target = returnFocusRef.current;
      returnFocusRef.current = null;
      if (target && document.contains(target)) target.focus();
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
    // Rebuilt only when the location or language changes.
  }, [location.lat, location.lon, t]);

  // 2. AED layers: ranked pins 1..5 + clustered rest.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !features) return;
    let cancelled = false;
    const layers: L.Layer[] = [];
    const ranked = rankedRef.current;
    ranked.clear();

    loadClusterPlugin().then((LC) => {
      if (cancelled) return;
      const rankedIds = new Set(nearest.map((item) => item.feature.id));
      const cluster = LC.markerClusterGroup({
        chunkedLoading: true,
        showCoverageOnHover: false,
        maxClusterRadius: 60,
        iconCreateFunction: (group: { getChildCount: () => number }) => {
          const count = group.getChildCount();
          const size = count < 100 ? 44 : count < 1000 ? 52 : 60;
          return L.divIcon({
            className: "",
            html: `<span class="aed-cluster" style="width:${size}px;height:${size}px"><span aria-hidden="true">${count}</span><span class="sr-only">${escapeHtml(t("Group of {0} AEDs – zoom in", { 0: count }))}</span></span>`,
            iconSize: [size, size],
          });
        },
      });
      const markers: L.Marker[] = [];
      for (const feature of features) {
        if (rankedIds.has(feature.id)) continue;
        const [lon, lat] = feature.geometry.coordinates;
        if (!Number.isFinite(lat) || !Number.isFinite(lon)) continue;
        const title = aedTitle(feature.properties) ?? t("AED defibrillator");
        const marker = L.marker([lat, lon], { icon: aedIcon(t, title), keyboard: true });
        marker.bindPopup(() => buildPopup(feature, null, location, t, locale), { maxWidth: 300 });
        markers.push(marker);
      }
      cluster.addLayers(markers);
      cluster.addTo(map);
      layers.push(cluster);

      for (const item of nearest) {
        const { lat, lon } = featureLatLon(item.feature);
        const title = aedTitle(item.feature.properties) ?? t("AED defibrillator");
        const selected = selectedRef.current === item.feature.id;
        const marker = L.marker([lat, lon], {
          icon: rankedIcon(item.rank, selected, t, title),
          keyboard: true,
          zIndexOffset: 2000 - item.rank,
        });
        marker.bindPopup(() => buildPopup(item.feature, item.rank, location, t, locale), {
          maxWidth: 300,
        });
        marker.on("click", () => onSelectRef.current(item.feature.id));
        marker.on("popupclose", () => {
          if (selectedRef.current === item.feature.id) onSelectRef.current(null);
        });
        marker.addTo(map);
        layers.push(marker);
        ranked.set(item.feature.id, { marker, rank: item.rank, title });
      }

      if (nearest.length > 0) {
        const bounds = L.latLngBounds([[location.lat, location.lon]]);
        nearest.forEach((item) => {
          const { lat, lon } = featureLatLon(item.feature);
          bounds.extend([lat, lon]);
        });
        map.fitBounds(bounds, {
          paddingTopLeft: fitPaddingRef.current ?? [48, 48],
          paddingBottomRight: [48, 48],
          maxZoom: 17,
          animate: false,
        });
      }
    });

    return () => {
      cancelled = true;
      layers.forEach((layer) => layer.remove());
      ranked.clear();
    };
  }, [features, nearest, location, t, locale]);

  // 3. Selection from the list / card: highlight pin N, open its popup, focus its heading.
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    rankedRef.current.forEach(({ marker, rank, title }, id) => {
      marker.setIcon(rankedIcon(rank, id === selectedId, t, title));
    });
    if (!selectedId) return;
    const entry = rankedRef.current.get(selectedId);
    if (!entry) return;
    if (entry.marker.isPopupOpen()) return;
    map.closePopup(); // fires popupclose (restores the previous focus target) before we store a new one
    const active = document.activeElement;
    returnFocusRef.current =
      active instanceof HTMLElement && !containerRef.current?.contains(active) ? active : null;
    map.panTo(entry.marker.getLatLng(), { animate: !prefersReducedMotion() });
    entry.marker.openPopup();
    const heading = entry.marker
      .getPopup()
      ?.getElement()
      ?.querySelector<HTMLElement>("[data-popup-heading]");
    heading?.focus();
  }, [selectedId, t]);

  return (
    <div
      ref={containerRef}
      role="region"
      aria-label={t("Map of defibrillators")}
      className="h-full w-full"
    />
  );
}

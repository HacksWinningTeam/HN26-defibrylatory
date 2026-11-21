"use client";

import { useEffect, useId, useState, useSyncExternalStore } from "react";
import { useTranslations } from "@/i18n/provider";
import {
  APPEARANCE_PREFERENCES,
  TEXT_SCALES,
  type AppearancePreference,
  type TextScale,
} from "./preferences";
import { useAccessibilityPreferences } from "./AccessibilityProvider";

function subscribeToSpeechSupport() {
  return () => {};
}

function getSpeechSupport() {
  return typeof window !== "undefined" && "speechSynthesis" in window;
}

function getServerSpeechSupport() {
  return false;
}

type AccessibilityPreferencesControlsProps = {
  layout?: "compact" | "settings";
};

export function AccessibilityPreferencesControls({
  layout = "compact",
}: AccessibilityPreferencesControlsProps) {
  const t = useTranslations();
  const appearanceLabels: Record<AppearancePreference, string> = {
    system: t("System"),
    light: t("Light"),
    dark: t("Dark"),
    "hc-black-white": t("High contrast: Black & White"),
    "hc-black-yellow": t("High contrast: Black & Yellow"),
    grayscale: t("Grayscale"),
  };

  const {
    appearance,
    textScale,
    underlineLinks,
    setAppearance,
    setTextScale,
    setUnderlineLinks,
    resetTextScale,
    resetSettings,
  } = useAccessibilityPreferences();

  const isSpeechSupported = useSyncExternalStore(
    subscribeToSpeechSupport,
    getSpeechSupport,
    getServerSpeechSupport,
  );
  const [isReading, setIsReading] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [speechStatus, setSpeechStatus] = useState(() => t("Ready to read"));
  const sectionId = useId();

  const textScaleIndex = TEXT_SCALES.indexOf(textScale);
  const canDecrease = textScaleIndex > 0;
  const canIncrease = textScaleIndex < TEXT_SCALES.length - 1;

  useEffect(() => {
    return () => {
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  function decreaseTextSize() {
    if (canDecrease) {
      setTextScale(TEXT_SCALES[textScaleIndex - 1] as TextScale);
    }
  }

  function increaseTextSize() {
    if (canIncrease) {
      setTextScale(TEXT_SCALES[textScaleIndex + 1] as TextScale);
    }
  }

  function toggleReadAloud() {
    if (!isSpeechSupported) return;

    if (isReading) {
      if (isPaused) {
        window.speechSynthesis.resume();
        setIsPaused(false);
        setSpeechStatus(t("Reading"));
      } else {
        window.speechSynthesis.pause();
        setIsPaused(true);
        setSpeechStatus(t("Reading paused"));
      }
      return;
    }

    const readableContent = document.querySelector("main")?.textContent?.trim();
    if (!readableContent) {
      setSpeechStatus(t("No readable content found"));
      return;
    }

    const utterance = new SpeechSynthesisUtterance(readableContent);
    utterance.lang = document.documentElement.lang || "pl-PL";
    utterance.onend = () => {
      setIsReading(false);
      setIsPaused(false);
      setSpeechStatus(t("Finished reading"));
    };
    utterance.onerror = () => {
      setIsReading(false);
      setIsPaused(false);
      setSpeechStatus(t("Read aloud is unavailable"));
    };

    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
    setIsReading(true);
    setIsPaused(false);
    setSpeechStatus(t("Reading"));
  }

  function stopReading() {
    if (!isSpeechSupported) return;
    window.speechSynthesis.cancel();
    setIsReading(false);
    setIsPaused(false);
    setSpeechStatus(t("Stop reading"));
  }

  const isSettings = layout === "settings";
  const headingClass = isSettings
    ? "text-base font-bold text-[var(--color-text)]"
    : "text-sm font-bold text-[var(--color-text)]";

  return (
    <div className={isSettings ? "space-y-6" : "space-y-4"}>
      <section aria-labelledby={`${sectionId}-display`} className="space-y-2">
        <div>
          <h3 id={`${sectionId}-display`} className={headingClass}>
            {t("Display mode")}
          </h3>
          {isSettings ? (
            <p className="text-sm text-[var(--color-text-muted)]">
              {t("Choose a color theme or high-contrast palette.")}
            </p>
          ) : null}
        </div>
        <fieldset>
          <legend className="sr-only">{t("Display mode")}</legend>
          <div className="grid grid-cols-1 gap-1.5 sm:grid-cols-2">
            {APPEARANCE_PREFERENCES.map((option) => (
              <label
                key={option}
                className={`flex min-h-11 cursor-pointer items-center gap-2 rounded-md border-2 px-3 py-2 text-sm font-medium transition-colors ${
                  appearance === option
                    ? "border-[var(--color-accent)] bg-[var(--color-surface-raised)] text-[var(--color-text)]"
                    : "border-[var(--color-border-subtle)] bg-[var(--color-surface)] text-[var(--color-text)] hover:border-[var(--color-border)]"
                }`}
              >
                <input
                  type="radio"
                  name={`${sectionId}-appearance`}
                  value={option}
                  checked={appearance === option}
                  onChange={() => setAppearance(option)}
                  className="h-4 w-4 accent-[var(--color-accent)]"
                />
                <span>{appearanceLabels[option]}</span>
              </label>
            ))}
          </div>
        </fieldset>
      </section>

      <section aria-labelledby={`${sectionId}-text`} className="space-y-2">
        <div>
          <h3 id={`${sectionId}-text`} className={headingClass}>
            {t("Text size")}
          </h3>
          {isSettings ? (
            <p className="text-sm text-[var(--color-text-muted)]">
              {t("Adjust base text scale from 25% to 200%.")}
            </p>
          ) : null}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={decreaseTextSize}
            disabled={!canDecrease}
            aria-label={t("Decrease text size")}
            className="inline-flex min-h-11 min-w-11 cursor-pointer items-center justify-center rounded-md border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-3 text-sm font-bold text-[var(--color-text)] transition-colors hover:border-[var(--color-accent)] disabled:cursor-not-allowed disabled:opacity-50"
          >
            <span aria-hidden="true">A&minus;</span>
          </button>
          <output
            aria-live="polite"
            aria-atomic="true"
            className="inline-flex min-h-11 items-center rounded-md border border-[var(--color-border-subtle)] bg-[var(--color-surface-raised)] px-3 text-sm font-semibold text-[var(--color-text)]"
          >
            {t("Text size: {0}%", { 0: textScale })}
          </output>
          <button
            type="button"
            onClick={increaseTextSize}
            disabled={!canIncrease}
            aria-label={t("Increase text size")}
            className="inline-flex min-h-11 min-w-11 cursor-pointer items-center justify-center rounded-md border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-3 text-sm font-bold text-[var(--color-text)] transition-colors hover:border-[var(--color-accent)] disabled:cursor-not-allowed disabled:opacity-50"
          >
            <span aria-hidden="true">A+</span>
          </button>
          <button
            type="button"
            onClick={resetTextScale}
            disabled={textScale === 100}
            className="inline-flex min-h-11 cursor-pointer items-center justify-center rounded-md border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-3 text-sm font-medium text-[var(--color-text)] transition-colors hover:border-[var(--color-accent)] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {t("Reset text size")}
          </button>
        </div>
      </section>

      <section aria-labelledby={`${sectionId}-links`} className="space-y-2">
        <div>
          <h3 id={`${sectionId}-links`} className={headingClass}>
            {t("Links")}
          </h3>
          {isSettings ? (
            <p className="text-sm text-[var(--color-text-muted)]">
              {t("Always underline links across the interface.")}
            </p>
          ) : null}
        </div>
        <label className="flex min-h-11 cursor-pointer items-center justify-between gap-3 rounded-md border-2 border-[var(--color-border-subtle)] bg-[var(--color-surface)] px-3 py-2 text-sm font-medium text-[var(--color-text)] hover:border-[var(--color-border)]">
          <span>{t("Underline links")}</span>
          <input
            type="checkbox"
            role="switch"
            checked={underlineLinks}
            onChange={(event) => setUnderlineLinks(event.target.checked)}
            className="h-5 w-5 accent-[var(--color-accent)]"
          />
        </label>
      </section>

      <section aria-labelledby={`${sectionId}-read`} className="space-y-2">
        <div>
          <h3 id={`${sectionId}-read`} className={headingClass}>
            {t("Read aloud")}
          </h3>
          {isSettings ? (
            <p className="text-sm text-[var(--color-text-muted)]">
              {t("Listen to the main page content using browser speech synthesis.")}
            </p>
          ) : null}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={toggleReadAloud}
            disabled={!isSpeechSupported}
            className="inline-flex min-h-11 cursor-pointer items-center justify-center rounded-md bg-[var(--color-accent)] px-4 py-2 text-sm font-semibold text-[var(--color-on-accent)] transition-colors hover:bg-[var(--color-accent-hover)] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isReading
              ? isPaused
                ? t("Resume")
                : t("Pause")
              : t("Read this page")}
          </button>
          <button
            type="button"
            onClick={stopReading}
            disabled={!isReading}
            aria-label={t("Stop reading")}
            className="inline-flex min-h-11 cursor-pointer items-center justify-center rounded-md border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2 text-sm font-medium text-[var(--color-text)] transition-colors hover:border-[var(--color-accent)] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {t("Stop")}
          </button>
        </div>
        <p aria-live="polite" aria-atomic="true" className="sr-only">
          {isSpeechSupported
            ? speechStatus
            : t("Read aloud is not supported in this browser")}
        </p>
      </section>

      <section aria-labelledby={`${sectionId}-reset`} className="space-y-2 border-t border-[var(--color-border-subtle)] pt-4">
        <div>
          <h3 id={`${sectionId}-reset`} className="sr-only">
            {t("Reset")}
          </h3>
          {isSettings ? (
            <p className="text-sm text-[var(--color-text-muted)]">
              {t("Restore default appearance, 100% text size, and default links.")}
            </p>
          ) : null}
        </div>
        <button
          type="button"
          onClick={resetSettings}
          className="inline-flex min-h-11 cursor-pointer items-center justify-center rounded-md border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2 text-sm font-semibold text-[var(--color-text)] transition-colors hover:border-[var(--color-accent)]"
        >
          {t("Reset settings")}
        </button>
      </section>
    </div>
  );
}

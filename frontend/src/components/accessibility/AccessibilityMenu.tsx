"use client";

import { useEffect, useId, useRef, useState } from "react";
import { usePathname } from "next/navigation";
import { useTranslations } from "@/i18n/provider";
import { AccessibilityIcon } from "./AccessibilityIcon";
import { AccessibilityPreferencesControls } from "./AccessibilityPreferencesControls";

export function AccessibilityMenu() {
  const t = useTranslations();
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const launcherRef = useRef<HTMLButtonElement>(null);
  const panelId = useId();
  const titleId = useId();

  useEffect(() => {
    if (!isOpen) return;
    const frame = window.requestAnimationFrame(() => {
      rootRef.current
        ?.querySelector<HTMLInputElement>('input[type="radio"]:checked')
        ?.focus();
    });
    return () => window.cancelAnimationFrame(frame);
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;
    const closeOnOutsidePointer = (event: PointerEvent) => {
      const target = event.target;
      if (target instanceof Node && !rootRef.current?.contains(target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("pointerdown", closeOnOutsidePointer);
    return () =>
      document.removeEventListener("pointerdown", closeOnOutsidePointer);
  }, [isOpen]);

  function closeAndRestoreFocus() {
    setIsOpen(false);
    window.requestAnimationFrame(() => launcherRef.current?.focus());
  }

  function handleLauncherClick() {
    if (isOpen) {
      closeAndRestoreFocus();
    } else {
      setIsOpen(true);
    }
  }

  function handlePanelKeyDown(event: React.KeyboardEvent<HTMLElement>) {
    if (event.key === "Escape") {
      event.preventDefault();
      closeAndRestoreFocus();
    }
  }

  if (pathname === "/settings/accessibility") return null;

  return (
    <div ref={rootRef} className="fixed right-4 bottom-4 z-40">
      <section
        id={panelId}
        role="dialog"
        aria-labelledby={titleId}
        hidden={!isOpen}
        onKeyDown={handlePanelKeyDown}
        className="mb-3 max-h-[80vh] w-[min(24rem,calc(100vw-2rem))] overflow-y-auto rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-xl"
      >
        <div className="mb-4 flex items-center justify-between gap-2 border-b border-[var(--color-border-subtle)] pb-3">
          <h2 id={titleId} className="text-base font-bold text-[var(--color-text)]">
            {t("Accessibility")}
          </h2>
          <button
            type="button"
            onClick={closeAndRestoreFocus}
            aria-label={t("Close accessibility menu")}
            className="inline-flex min-h-11 min-w-11 cursor-pointer items-center justify-center rounded-md border border-[var(--color-border)] bg-[var(--color-surface-raised)] text-lg font-bold text-[var(--color-text)] hover:border-[var(--color-accent)]"
          >
            <span aria-hidden="true">&times;</span>
          </button>
        </div>
        <AccessibilityPreferencesControls layout="compact" />
      </section>

      <div className="flex justify-end">
        <button
          ref={launcherRef}
          type="button"
          onClick={handleLauncherClick}
          aria-expanded={isOpen}
          aria-controls={panelId}
          aria-label={t("Open accessibility menu")}
          className="inline-flex min-h-11 cursor-pointer items-center gap-2 rounded-full border-2 border-[var(--color-border)] bg-[var(--color-accent)] px-4 py-2 text-sm font-semibold text-[var(--color-on-accent)] shadow-lg transition-colors hover:bg-[var(--color-accent-hover)]"
        >
          <AccessibilityIcon className="h-5 w-5" />
          <span>{t("Accessibility")}</span>
        </button>
      </div>
    </div>
  );
}

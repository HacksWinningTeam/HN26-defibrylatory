"use client";

import { useId, useState, useTransition } from "react";
import { saveLocale } from "./actions";
import { isLocale } from "./locale";
import { useLocale, useTranslations } from "./provider";

export type LanguageSelectorProps = {
  hideLabel?: boolean;
  className?: string;
};

export function LanguageSelector({
  hideLabel = false,
  className,
}: LanguageSelectorProps = {}) {
  const locale = useLocale();
  const t = useTranslations();
  const [pending, startTransition] = useTransition();
  const [failed, setFailed] = useState(false);
  const selectId = useId();
  const errorId = useId();

  return (
    <div className={["inline-flex flex-col gap-1", className].filter(Boolean).join(" ")}>
      <div className="inline-flex items-center gap-2">
        <label
          htmlFor={selectId}
          className={
            hideLabel
              ? "sr-only"
              : "text-sm font-medium text-[var(--color-text-muted)]"
          }
        >
          {t("Language")}
        </label>
        <select
          id={selectId}
          value={locale}
          disabled={pending}
          aria-invalid={failed || undefined}
          aria-describedby={failed ? errorId : undefined}
          onChange={(event) => {
            const value = event.target.value;
            if (!isLocale(value) || value === locale) return;
            setFailed(false);
            startTransition(async () => {
              try {
                await saveLocale(value);
              } catch {
                setFailed(true);
              }
            });
          }}
          className="min-h-11 cursor-pointer rounded-md border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm font-medium text-[var(--color-text)] transition-colors hover:border-[var(--color-accent)] disabled:cursor-not-allowed disabled:opacity-60"
        >
          <option value="en-US">English (US)</option>
          <option value="pl-PL">Polski</option>
        </select>
      </div>
      {pending ? (
        <p className="text-xs text-[var(--color-text-muted)]" role="status">
          {t("Saving…")}
        </p>
      ) : null}
      {failed ? (
        <p id={errorId} className="text-xs font-medium text-[var(--color-error-text)]" role="alert">
          {t("The language could not be saved. Try again.")}
        </p>
      ) : null}
    </div>
  );
}

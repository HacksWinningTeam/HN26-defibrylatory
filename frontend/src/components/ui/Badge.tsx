import type { ReactNode } from "react";

export type BadgeVariant = "neutral" | "success" | "warning" | "error";

const VARIANT_CLASSES: Record<BadgeVariant, string> = {
  neutral:
    "border-[var(--color-border)] bg-[var(--color-surface-raised)] text-[var(--color-text)]",
  success:
    "border-[var(--color-success-badge)] bg-[var(--color-success-badge)] text-[var(--color-success-on-badge)]",
  warning:
    "border-[var(--color-warning-badge)] bg-[var(--color-warning-badge)] text-[var(--color-warning-on-badge)]",
  error:
    "border-[var(--color-error-badge)] bg-[var(--color-error-badge)] text-[var(--color-error-on-badge)]",
};

/** Status pill. Always icon + text, never colour alone (WCAG 1.4.1). */
export function Badge({
  variant,
  icon,
  children,
}: {
  variant: BadgeVariant;
  icon: ReactNode;
  children: ReactNode;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-sm font-semibold ${VARIANT_CLASSES[variant]}`}
    >
      <span aria-hidden="true">{icon}</span>
      <span>{children}</span>
    </span>
  );
}

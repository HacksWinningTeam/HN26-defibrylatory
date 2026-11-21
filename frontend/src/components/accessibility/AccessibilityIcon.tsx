export function AccessibilityIcon({ className }: { className?: string }) {
  return (
    <svg
      aria-hidden="true"
      className={className}
      fill="none"
      focusable="false"
      height="20"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="2"
      viewBox="0 0 24 24"
      width="20"
    >
      <circle cx="12" cy="4.5" r="1.75" />
      <path d="M5 8.5h14" />
      <path d="M12 8.5v5.5" />
      <path d="m9 20 3-6 3 6" />
    </svg>
  );
}

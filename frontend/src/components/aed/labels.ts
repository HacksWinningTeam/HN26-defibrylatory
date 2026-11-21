import type { MessageKey } from "@/i18n/messages";
import type { BadgeKind } from "@/lib/aed";

/** Message keys without `{n}` placeholders, so `t(key)` needs no arguments. */
export type PlainMessageKey = Exclude<MessageKey, `${string}{${string}}${string}`>;

/** Badge text + icon (icons are decorative; the text carries the meaning). */
export const BADGE_LABELS: Record<BadgeKind, { label: PlainMessageKey; icon: string }> = {
  locked: { label: "Locked with a key", icon: "🔒" },
  code: { label: "Code-locked cabinet", icon: "🔢" },
  public: { label: "Public", icon: "✔" },
  restricted: { label: "Restricted access", icon: "⚠" },
  private: { label: "Not public", icon: "⛔" },
  "access-unknown": { label: "Access: no information", icon: "?" },
  h24: { label: "24/7", icon: "🕑" },
  "out-of-service": { label: "May be out of service", icon: "⚠" },
};

/** schema.py enum codes -> UI labels; unknown codes are shown verbatim, "nieznany" as "no information". */
export const DOSTEP_LABELS: Record<string, PlainMessageKey> = {
  publiczny: "Open to everyone",
  ograniczony: "Restricted (staff/customers or on request)",
  prywatny: "Not publicly accessible",
  nieznany: "no information",
};

export const ZABEZPIECZENIE_LABELS: Record<string, PlainMessageKey> = {
  brak: "No cabinet",
  szafka_otwarta: "Cabinet without lock",
  szafka_z_alarmem: "Cabinet with alarm",
  szafka_na_kod: "Code-locked cabinet (code from the 112 dispatcher)",
  zamkniety_na_klucz: "Locked with a key – ask the staff",
  nieznany: "no information",
};

export const STATUS_LABELS: Record<string, PlainMessageKey> = {
  sprawny: "Working",
  niesprawny: "Out of order",
  w_serwisie: "In service",
  do_weryfikacji: "To be checked",
  skradziony: "Stolen / missing",
  wycofany: "Withdrawn",
  nieznany: "no information",
};

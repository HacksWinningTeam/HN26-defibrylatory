/** Browser-only UI preferences stored in localStorage with cross-tab and same-tab sync. */
const CHANGE_EVENT = "hn26-preference-change";

export function subscribeToPreferences(onChange: () => void): () => void {
  window.addEventListener("storage", onChange);
  window.addEventListener(CHANGE_EVENT, onChange);
  return () => {
    window.removeEventListener("storage", onChange);
    window.removeEventListener(CHANGE_EVENT, onChange);
  };
}

export function readPreference(key: string): string | null {
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

export function savePreference(key: string, value: string): void {
  // Notify subscribers only after persistence succeeds so a failed save
  // retains the current selection and lets the selector show a retry message.
  window.localStorage.setItem(key, value);
  window.dispatchEvent(new Event(CHANGE_EVENT));
}

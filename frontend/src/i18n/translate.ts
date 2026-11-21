import { defaultLocale, type Locale } from "./locale";
import { english, polish, type MessageKey } from "./messages";

type Slots<S extends string> = S extends `${string}{${infer P}}${infer Rest}`
  ? P | Slots<Rest>
  : never;

type Arguments<K extends MessageKey> = [Slots<K>] extends [never]
  ? []
  : [values: Record<Slots<K>, string | number>];

export type Translator = <K extends MessageKey>(
  key: K,
  ...args: Arguments<K>
) => string;

export function createTranslator(locale: Locale = defaultLocale): Translator {
  return (key, ...args) => {
    const message: string = locale === "pl-PL" ? polish[key] : english[key];
    return message.replace(/\{(\w+)\}/g, (_, name: string) => {
      const value = (
        args[0] as Record<string, string | number> | undefined
      )?.[name];
      if (value === undefined) {
        throw new Error(`Missing translation parameter: ${name}`);
      }
      return String(value);
    });
  };
}

/** Only for component-owned, parameter-free messages returned by pure models. */
export function translateModelMessage(locale: Locale, message: string): string {
  return Object.hasOwn(polish, message)
    ? locale === "pl-PL"
      ? polish[message as MessageKey]
      : message
    : message;
}

import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import { defaultAppearance, themeColors } from "@/appearance/appearance";
import { AccessibilityProvider } from "@/components/accessibility/AccessibilityProvider";
import { AppShell } from "@/components/AppShell";
import { defaultLocale } from "@/i18n/locale";
import { LocaleProvider } from "@/i18n/provider";
import { getPrehydrateScript } from "@/lib/prehydrate";

import "./globals.css";

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: themeColors.light },
    { media: "(prefers-color-scheme: dark)", color: themeColors.dark },
  ],
};

export const metadata: Metadata = {
  title: "Misja AED – najbliższy defibrylator",
  description:
    "Najbliższy defibrylator AED z ogólnopolskiego zbioru scalonego z danych dane.gov.pl i OpenStreetMap.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  const locale = defaultLocale;
  const appearance = defaultAppearance;

  return (
    <html
      suppressHydrationWarning
      data-appearance={appearance}
      lang={locale}
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: getPrehydrateScript() }} />
      </head>
      <body className="flex min-h-screen flex-col bg-[var(--color-canvas)] font-sans text-[var(--color-text)] antialiased">
        <LocaleProvider locale={locale}>
          <AccessibilityProvider>
            <AppShell>{children}</AppShell>
          </AccessibilityProvider>
        </LocaleProvider>
      </body>
    </html>
  );
}

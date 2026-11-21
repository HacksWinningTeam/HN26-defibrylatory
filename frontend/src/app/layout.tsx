import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  title: "Django + DRF + Next.js Template",
  description:
    "Dockerized application template powered by Django, Django REST Framework, PostgreSQL, and Next.js.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="flex min-h-screen flex-col bg-slate-50 font-sans text-slate-900 antialiased">
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:inline-flex focus:min-h-11 focus:items-center focus:rounded-md focus:bg-blue-700 focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-white focus:shadow-md"
        >
          Skip to main content
        </a>

        <header className="border-b border-slate-300 bg-white">
          <div className="mx-auto flex w-full max-w-4xl flex-wrap items-center justify-between gap-4 px-6 py-4">
            <p className="text-base font-bold tracking-tight text-slate-900">
              Django + DRF + Next.js
            </p>
            <p className="text-sm font-medium text-slate-700">
              Docker Full-Stack Template
            </p>
          </div>
        </header>

        <main id="main-content" className="mx-auto w-full max-w-4xl flex-1 px-6 py-10">
          {children}
        </main>

        <footer className="border-t border-slate-300 bg-white">
          <div className="mx-auto w-full max-w-4xl px-6 py-4 text-sm text-slate-700">
            Django 5.2 LTS &middot; Django REST Framework &middot; drf-spectacular &middot;
            PostgreSQL 18 &middot; Next.js 16
          </div>
        </footer>
      </body>
    </html>
  );
}

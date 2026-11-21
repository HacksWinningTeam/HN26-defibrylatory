"use client";

import { useState } from "react";

import { fetchHealth, type HealthCheckResult } from "@/lib/api";

interface HealthStatusCardProps {
  initialResult: HealthCheckResult;
  publicApiUrl: string;
}

export function HealthStatusCard({
  initialResult,
  publicApiUrl,
}: Readonly<HealthStatusCardProps>) {
  const [result, setResult] = useState<HealthCheckResult>(initialResult);
  const [source, setSource] = useState<"server" | "browser">("server");
  const [isChecking, setIsChecking] = useState(false);

  async function handleRecheck() {
    setIsChecking(true);
    const nextResult = await fetchHealth();
    setResult(nextResult);
    setSource("browser");
    setIsChecking(false);
  }

  const isHealthy = result.ok;
  const apiLabel = isHealthy ? "Healthy" : result.data ? "Degraded" : "Unreachable";
  const dbLabel =
    result.data?.database === "ok"
      ? "Connected"
      : result.data?.database === "error"
        ? "Error"
        : "Unknown";

  return (
    <section
      aria-labelledby="health-heading"
      className="rounded-lg border-2 border-slate-400 bg-white p-6 shadow-xs"
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 id="health-heading" className="text-xl font-bold text-slate-900">
            Backend &amp; Database Connectivity
          </h2>
          <p className="mt-1 text-sm text-slate-700">
            Verified via{" "}
            <code className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-xs text-slate-900">
              {publicApiUrl}/api/health/
            </code>
          </p>
        </div>

        <button
          type="button"
          onClick={handleRecheck}
          disabled={isChecking}
          aria-busy={isChecking}
          className="inline-flex min-h-11 cursor-pointer items-center justify-center rounded-md bg-blue-700 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-blue-800 disabled:cursor-not-allowed disabled:bg-slate-600"
        >
          {isChecking ? "Checking API..." : "Re-check API"}
        </button>
      </div>

      <div
        role="status"
        aria-live="polite"
        className={`mt-5 rounded-md border-2 p-4 ${
          isHealthy
            ? "border-emerald-700 bg-emerald-50 text-emerald-950"
            : "border-red-700 bg-red-50 text-red-950"
        }`}
      >
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="text-base font-bold">
            <span
              className={`mr-2 inline-block rounded px-2 py-0.5 font-mono text-xs font-bold uppercase ${
                isHealthy
                  ? "bg-emerald-800 text-white"
                  : "bg-red-800 text-white"
              }`}
            >
              {isHealthy ? "PASS" : "FAIL"}
            </span>
            API Status: {apiLabel}
          </p>
          <span className="text-xs font-semibold uppercase tracking-wide">
            Source:{" "}
            {source === "server"
              ? "Server SSR"
              : publicApiUrl
                ? "Browser Fetch (CORS)"
                : "Browser Fetch (Same-Origin Proxy)"}
          </span>
        </div>

        <dl className="mt-4 grid grid-cols-1 gap-3 text-sm sm:grid-cols-3">
          <div>
            <dt className="font-semibold">HTTP Status</dt>
            <dd className="mt-0.5 font-mono">
              {result.statusCode !== null ? result.statusCode : "No response"}
            </dd>
          </div>
          <div>
            <dt className="font-semibold">PostgreSQL Database</dt>
            <dd className="mt-0.5 font-mono">{dbLabel}</dd>
          </div>
          <div>
            <dt className="font-semibold">Server Timestamp (UTC)</dt>
            <dd className="mt-0.5 font-mono break-all">
              {result.data?.timestamp ?? "N/A"}
            </dd>
          </div>
        </dl>

        {result.error ? (
          <p className="mt-3 border-t border-red-300 pt-3 text-sm font-medium">
            Detail: {result.error}
          </p>
        ) : null}
      </div>
    </section>
  );
}

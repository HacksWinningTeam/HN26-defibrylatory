import { HealthStatusCard } from "@/components/HealthStatusCard";
import { fetchHealth, getPublicApiBaseUrl } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const initialHealth = await fetchHealth();
  const publicApiUrl = getPublicApiBaseUrl();

  const quickLinks = [
    {
      label: "Swagger UI",
      description: "Interactive OpenAPI 3 documentation",
      href: `${publicApiUrl}/api/docs/`,
    },
    {
      label: "ReDoc",
      description: "Clean API reference powered by drf-spectacular",
      href: `${publicApiUrl}/api/redoc/`,
    },
    {
      label: "OpenAPI Schema",
      description: "Raw OpenAPI 3 specification",
      href: `${publicApiUrl}/api/schema/`,
    },
    {
      label: "Django Admin",
      description: "Built-in administrative console",
      href: `${publicApiUrl}/admin/`,
    },
  ];

  return (
    <div className="space-y-8">
      <section aria-labelledby="intro-heading" className="space-y-3">
        <h1
          id="intro-heading"
          className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl"
        >
          Full-Stack Docker Template Ready
        </h1>
        <p className="max-w-2xl text-base leading-relaxed text-slate-700">
          This starter pairs a Django 5.2 LTS and Django REST Framework backend
          with a Next.js 16 App Router frontend and PostgreSQL 18, wired
          together for both local hot-reload development and production builds.
        </p>
      </section>

      <HealthStatusCard
        initialResult={initialHealth}
        publicApiUrl={publicApiUrl}
      />

      <section aria-labelledby="links-heading" className="space-y-4">
        <h2 id="links-heading" className="text-xl font-bold text-slate-900">
          API Documentation &amp; Admin Links
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {quickLinks.map((item) => (
            <a
              key={item.href}
              href={item.href}
              target="_blank"
              rel="noopener noreferrer"
              className="flex min-h-11 flex-col justify-between rounded-lg border-2 border-slate-400 bg-white p-4 transition-colors hover:border-blue-700 hover:bg-slate-50"
            >
              <span className="text-base font-bold text-blue-800 underline decoration-2 underline-offset-2">
                {item.label}
              </span>
              <span className="mt-1 text-sm text-slate-700">
                {item.description}
              </span>
            </a>
          ))}
        </div>
      </section>
    </div>
  );
}

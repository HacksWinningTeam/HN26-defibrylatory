import { EmergencyBanner } from "@/components/EmergencyBanner";
import { AedFinder } from "@/components/aed/AedFinder";
import { DataInfo } from "@/components/aed/DataInfo";
import { parseLocationParams } from "@/lib/aed";
import { fetchSources } from "@/lib/api";
import { fetchPortalSources, getPortalApiUrl } from "@/lib/portal";

export const dynamic = "force-dynamic";

/** "Najbliższy AED" from the demo location (BCTW Bydgoszcz), DEC-010. */
export default async function HomePage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const location = parseLocationParams(await searchParams);
  // T15 / DEC-014: data from the dane.gov.pl fork when DANEGOV_API_URL is set, else the old backend.
  const portalApiUrl = getPortalApiUrl();
  const portal = portalApiUrl ? await fetchPortalSources() : null;
  const report = portal ? portal.report : portalApiUrl ? null : await fetchSources();
  const forkUrl = process.env.DANEGOV_FORK_URL?.trim() || portal?.datasetUrl || null;

  return (
    <div className="flex flex-col gap-6">
      <EmergencyBanner />
      <AedFinder location={location} />
      <DataInfo report={report} forkUrl={forkUrl} portalApiUrl={portalApiUrl} />
    </div>
  );
}

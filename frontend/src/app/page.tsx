import { EmergencyBanner } from "@/components/EmergencyBanner";
import { AedFinder } from "@/components/aed/AedFinder";
import { DataInfo } from "@/components/aed/DataInfo";
import { parseLocationParams } from "@/lib/aed";
import { fetchSources } from "@/lib/api";

export const dynamic = "force-dynamic";

/** "Najbliższy AED" from the demo location (BCTW Bydgoszcz), DEC-010. */
export default async function HomePage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const location = parseLocationParams(await searchParams);
  const report = await fetchSources();
  const forkUrl = process.env.DANEGOV_FORK_URL?.trim() || null;

  return (
    <div className="flex flex-col gap-6">
      <EmergencyBanner />
      <AedFinder location={location} />
      <DataInfo report={report} forkUrl={forkUrl} />
    </div>
  );
}

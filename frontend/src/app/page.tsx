import { MapFirstView } from "@/components/aed/MapFirstView";
import { parseLocationParams } from "@/lib/aed";

export const dynamic = "force-dynamic";

/** "/" (T21, DEC-021): map-first page — nearest AED from the demo location (BCTW Bydgoszcz, DEC-010). */
export default async function HomePage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const location = parseLocationParams(await searchParams);
  return <MapFirstView location={location} />;
}

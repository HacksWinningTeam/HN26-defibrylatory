import { HomeView } from "@/components/HomeView";
import { fetchHealth, getPublicApiBaseUrl } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const initialHealth = await fetchHealth();
  const publicApiUrl = getPublicApiBaseUrl();

  return (
    <HomeView
      initialHealth={initialHealth}
      publicApiUrl={publicApiUrl}
    />
  );
}

import { fetchActivities, type Activity } from "@/lib/api";
import { summarizeBySport } from "@/lib/summary";
import { SummaryCard } from "@/components/SummaryCard";
import { SportTabs } from "@/components/SportTabs";
import { ActivityTable } from "@/components/ActivityTable";

export default async function Home({
  searchParams,
}: {
  searchParams: Promise<{ sport?: string }>;
}) {
  const { sport } = await searchParams;
  const activeSport = sport ?? "All";

  let activities: Activity[] = [];
  let loadError: string | null = null;
  try {
    activities = await fetchActivities({ limit: 500 });
  } catch (err) {
    loadError =
      err instanceof Error
        ? err.message
        : "Unknown error fetching activities.";
  }

  const summaries = summarizeBySport(activities, 28);
  const visibleActivities =
    activeSport === "All" ? activities : activities.filter((a) => a.sport_type === activeSport);

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-50">Ironman Coach</h1>
      <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Last 28 days, by sport</p>

      {loadError ? (
        <div className="mt-6 rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-300">
          Couldn&apos;t reach the backend API: {loadError}
          <br />
          Make sure it&apos;s running (<code>uvicorn app.main:app --reload --port 8000</code> from{" "}
          <code>backend/</code>).
        </div>
      ) : (
        <>
          <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
            {summaries.length === 0 ? (
              <p className="text-sm text-slate-500 dark:text-slate-400">No activity in the last 28 days.</p>
            ) : (
              summaries.map((s) => <SummaryCard key={s.sportType} summary={s} />)
            )}
          </div>

          <div className="mt-10 flex flex-wrap items-center justify-between gap-4">
            <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-50">
              Recent activities
            </h2>
            <SportTabs active={activeSport} />
          </div>

          <div className="mt-4">
            <ActivityTable activities={visibleActivities} />
          </div>
        </>
      )}
    </main>
  );
}

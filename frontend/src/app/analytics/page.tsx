import Link from "next/link";
import { fetchWeeklyLoad, fetchTrends, type TrendPoint } from "@/lib/api";
import { WeeklyLoadChart } from "@/components/charts/WeeklyLoadChart";
import { TrendsSection } from "@/components/charts/TrendsSection";

export default async function AnalyticsPage() {
  let weeklyLoad: Awaited<ReturnType<typeof fetchWeeklyLoad>> = [];
  let trendsBySport: Record<"Run" | "Ride" | "Swim", TrendPoint[]> = { Run: [], Ride: [], Swim: [] };
  let loadError: string | null = null;

  try {
    const [weekly, run, ride, swim] = await Promise.all([
      fetchWeeklyLoad(12),
      fetchTrends("Run", 12),
      fetchTrends("Ride", 12),
      fetchTrends("Swim", 12),
    ]);
    weeklyLoad = weekly;
    trendsBySport = { Run: run, Ride: ride, Swim: swim };
  } catch (err) {
    loadError = err instanceof Error ? err.message : "Unknown error fetching analytics.";
  }

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <div className="flex items-baseline justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-50">Training Analytics</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Last 12 weeks</p>
        </div>
        <Link href="/" className="text-sm font-medium text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100">
          ← Dashboard
        </Link>
      </div>

      {loadError ? (
        <div className="mt-6 rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-300">
          Couldn&apos;t reach the backend API: {loadError}
        </div>
      ) : (
        <div className="mt-6 flex flex-col gap-6">
          <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900">
            <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-50">Weekly training load</h2>
            <p className="mt-0.5 text-xs text-slate-400 dark:text-slate-500">
              A relative estimate combining duration and heart-rate intensity — not a
              standardized score, useful for comparing your own weeks to each other.
            </p>
            <div className="mt-3">
              <WeeklyLoadChart data={weeklyLoad} />
            </div>
          </div>

          <TrendsSection trendsBySport={trendsBySport} />
        </div>
      )}
    </main>
  );
}

import Link from "next/link";
import {
  fetchActivities,
  fetchCurrentWeather,
  fetchReadiness,
  fetchTasks,
  fetchUpcomingEvents,
  type Activity,
  type CalendarEvent,
  type Readiness,
  type Task,
  type WeatherNow,
} from "@/lib/api";
import { summarizeBySport } from "@/lib/summary";
import { SummaryCard } from "@/components/SummaryCard";
import { SportTabs } from "@/components/SportTabs";
import { ActivityTable } from "@/components/ActivityTable";
import { WeatherCard } from "@/components/WeatherCard";
import { UpcomingEvents } from "@/components/UpcomingEvents";
import { ReadinessCard } from "@/components/ReadinessCard";
import { CoachCard } from "@/components/CoachCard";
import { TaskList } from "@/components/TaskList";

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

  // Weather is independent of activities -- don't let one failure take down
  // the other (e.g. no GPS-tagged activity yet to derive a location from).
  let weather: WeatherNow | null = null;
  let weatherError: string | null = null;
  try {
    weather = await fetchCurrentWeather();
  } catch (err) {
    weatherError = err instanceof Error ? err.message : "Unknown error fetching weather.";
  }

  // Same independence rule as weather -- calendar needs its own Google
  // OAuth connection, which may not be set up yet.
  let events: CalendarEvent[] = [];
  let eventsError: string | null = null;
  try {
    events = await fetchUpcomingEvents(7);
  } catch (err) {
    eventsError = err instanceof Error ? err.message : "Unknown error fetching calendar.";
  }

  let readiness: Readiness | null = null;
  let readinessError: string | null = null;
  try {
    readiness = await fetchReadiness();
  } catch (err) {
    readinessError = err instanceof Error ? err.message : "Unknown error fetching readiness.";
  }

  let tasks: Task[] = [];
  let tasksError: string | null = null;
  try {
    // include_completed=true -- TaskList sorts completed to the bottom and
    // shows them struck through, rather than hiding them the instant
    // they're checked off. See TaskList's refresh() for the same choice.
    tasks = await fetchTasks(true);
  } catch (err) {
    tasksError = err instanceof Error ? err.message : "Unknown error fetching tasks.";
  }

  const summaries = summarizeBySport(activities, 28);
  const visibleActivities =
    activeSport === "All" ? activities : activities.filter((a) => a.sport_type === activeSport);

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <div className="flex items-baseline justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-50">Ironman Coach</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Last 28 days, by sport</p>
        </div>
        <Link
          href="/analytics"
          className="text-sm font-medium text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
        >
          Analytics →
        </Link>
      </div>

      {loadError ? (
        <div className="mt-6 rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-300">
          Couldn&apos;t reach the backend API: {loadError}
          <br />
          Make sure it&apos;s running (<code>uvicorn app.main:app --reload --port 8000</code> from{" "}
          <code>backend/</code>).
        </div>
      ) : (
        <>
          <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-2">
            {readiness ? (
              <ReadinessCard readiness={readiness} />
            ) : (
              <p className="text-sm text-slate-400 dark:text-slate-500">
                Readiness unavailable{readinessError ? `: ${readinessError}` : ""}
              </p>
            )}
            <CoachCard />
          </div>

          <div className="mt-6">
            {tasksError ? (
              <p className="text-sm text-slate-400 dark:text-slate-500">
                Tasks unavailable: {tasksError}
              </p>
            ) : (
              <TaskList initialTasks={tasks} />
            )}
          </div>

          <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
            <div className="lg:col-span-2">
              {weather ? (
                <WeatherCard weather={weather} />
              ) : (
                <p className="text-sm text-slate-400 dark:text-slate-500">
                  Weather unavailable{weatherError ? `: ${weatherError}` : ""}
                </p>
              )}
            </div>

            <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900">
              <div className="text-sm font-medium text-slate-500 dark:text-slate-400">
                Next 7 days
              </div>
              <div className="mt-2">
                {eventsError ? (
                  <p className="text-sm text-slate-400 dark:text-slate-500">
                    Calendar not connected. See README to set up Google Calendar.
                  </p>
                ) : (
                  <UpcomingEvents events={events} />
                )}
              </div>
            </div>
          </div>

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

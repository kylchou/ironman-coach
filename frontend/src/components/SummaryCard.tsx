import { formatDistance, formatDuration } from "@/lib/format";
import type { SportSummary } from "@/lib/summary";

const ACCENTS: Record<string, string> = {
  Swim: "border-l-sky-500",
  Ride: "border-l-amber-500",
  Run: "border-l-rose-500",
};

export function SummaryCard({ summary }: { summary: SportSummary }) {
  const accent = ACCENTS[summary.sportType] ?? "border-l-slate-400";

  return (
    <div className={`rounded-lg border border-slate-200 border-l-4 ${accent} bg-white p-4 shadow-sm dark:bg-slate-900 dark:border-slate-700`}>
      <div className="text-sm font-medium text-slate-500 dark:text-slate-400">{summary.sportType}</div>
      <div className="mt-1 text-2xl font-semibold text-slate-900 dark:text-slate-50">
        {formatDistance(summary.totalDistanceM, summary.sportType)}
      </div>
      <div className="mt-1 text-sm text-slate-500 dark:text-slate-400">
        {summary.count} {summary.count === 1 ? "session" : "sessions"} · {formatDuration(summary.totalTimeS)}
      </div>
    </div>
  );
}

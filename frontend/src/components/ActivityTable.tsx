import { formatDate, formatDistance, formatDuration, formatPace } from "@/lib/format";
import type { Activity } from "@/lib/api";

const SPORT_BADGE: Record<string, string> = {
  Swim: "bg-sky-100 text-sky-700 dark:bg-sky-950 dark:text-sky-300",
  Ride: "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300",
  Run: "bg-rose-100 text-rose-700 dark:bg-rose-950 dark:text-rose-300",
};

export function ActivityTable({ activities }: { activities: Activity[] }) {
  if (activities.length === 0) {
    return <p className="text-sm text-slate-500 dark:text-slate-400">No activities found.</p>;
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700">
      <table className="w-full min-w-[720px] text-sm">
        <thead className="bg-slate-50 text-left text-slate-500 dark:bg-slate-800 dark:text-slate-400">
          <tr>
            <th className="px-4 py-2 font-medium">Date</th>
            <th className="px-4 py-2 font-medium">Activity</th>
            <th className="px-4 py-2 font-medium">Sport</th>
            <th className="px-4 py-2 font-medium">Distance</th>
            <th className="px-4 py-2 font-medium">Time</th>
            <th className="px-4 py-2 font-medium">Pace</th>
            <th className="px-4 py-2 font-medium">Avg HR</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
          {activities.map((a) => (
            <tr key={a.id} className="hover:bg-slate-50 dark:hover:bg-slate-900">
              <td className="whitespace-nowrap px-4 py-2 text-slate-500 dark:text-slate-400">
                {formatDate(a.start_date)}
              </td>
              <td className="px-4 py-2 font-medium text-slate-900 dark:text-slate-50">{a.name ?? "—"}</td>
              <td className="px-4 py-2">
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                    SPORT_BADGE[a.sport_type] ?? "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
                  }`}
                >
                  {a.sport_type}
                </span>
              </td>
              <td className="whitespace-nowrap px-4 py-2">{formatDistance(a.distance_m, a.sport_type)}</td>
              <td className="whitespace-nowrap px-4 py-2">{formatDuration(a.moving_time_s)}</td>
              <td className="whitespace-nowrap px-4 py-2">{formatPace(a.average_speed_mps, a.sport_type)}</td>
              <td className="whitespace-nowrap px-4 py-2">
                {a.average_heartrate != null ? `${Math.round(a.average_heartrate)} bpm` : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

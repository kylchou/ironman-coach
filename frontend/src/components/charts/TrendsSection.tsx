"use client";

import { useState } from "react";
import { LineChart } from "./LineChart";
import { formatWeekLabel, paceOrSpeedValue, paceOrSpeedAxisLabel, formatPaceOrSpeedValue } from "@/lib/format";
import type { TrendPoint } from "@/lib/api";

const SPORTS = ["Run", "Ride", "Swim"] as const;
type Sport = (typeof SPORTS)[number];

const COLOR_VAR: Record<Sport, string> = {
  Run: "var(--chart-run)",
  Ride: "var(--chart-ride)",
  Swim: "var(--chart-swim)",
};

export function TrendsSection({ trendsBySport }: { trendsBySport: Record<Sport, TrendPoint[]> }) {
  const [sport, setSport] = useState<Sport>("Run");
  const data = trendsBySport[sport];

  const paceData = data.map((d) => ({
    label: formatWeekLabel(d.week_start),
    value: paceOrSpeedValue(d.avg_speed_mps, sport),
  }));
  const hrData = data.map((d) => ({
    label: formatWeekLabel(d.week_start),
    value: d.avg_heartrate,
  }));

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-50">Trends</h3>
        <div className="flex gap-1 rounded-lg bg-slate-100 p-1 dark:bg-slate-800">
          {SPORTS.map((s) => (
            <button
              key={s}
              onClick={() => setSport(s)}
              className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                s === sport
                  ? "bg-white text-slate-900 shadow-sm dark:bg-slate-900 dark:text-slate-50"
                  : "text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-6 md:grid-cols-2">
        <LineChart
          title={paceOrSpeedAxisLabel(sport)}
          data={paceData}
          color={COLOR_VAR[sport]}
          formatValue={(v) => formatPaceOrSpeedValue(v, sport)}
        />
        <LineChart
          title="Average heart rate"
          data={hrData}
          color={COLOR_VAR[sport]}
          formatValue={(v) => `${Math.round(v)} bpm`}
        />
      </div>
    </div>
  );
}

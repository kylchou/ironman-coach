"use client";

import { useState } from "react";
import { formatWeekLabel } from "@/lib/format";
import type { WeeklyLoad } from "@/lib/api";

const SPORTS = ["Run", "Ride", "Swim"] as const;
const COLOR_VAR: Record<(typeof SPORTS)[number], string> = {
  Run: "var(--chart-run)",
  Ride: "var(--chart-ride)",
  Swim: "var(--chart-swim)",
};

const WIDTH = 720;
const HEIGHT = 260;
const PAD_LEFT = 44;
const PAD_BOTTOM = 28;
const PAD_TOP = 12;
const BAR_MAX_WIDTH = 24;
const SEGMENT_GAP = 2;

function niceMax(value: number): number {
  if (value <= 0) return 10;
  const magnitude = 10 ** Math.floor(Math.log10(value));
  const normalized = value / magnitude;
  const step = normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 5 ? 5 : 10;
  return step * magnitude;
}

export function WeeklyLoadChart({ data }: { data: WeeklyLoad[] }) {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  if (data.length === 0) {
    return <p className="text-sm text-slate-500 dark:text-slate-400">No training load data yet.</p>;
  }

  const plotWidth = WIDTH - PAD_LEFT - 12;
  const plotHeight = HEIGHT - PAD_TOP - PAD_BOTTOM;
  const bandWidth = plotWidth / data.length;
  const barWidth = Math.min(BAR_MAX_WIDTH, bandWidth * 0.6);

  const maxTotal = niceMax(Math.max(...data.map((d) => d.total_load)));
  const yScale = (v: number) => plotHeight - (v / maxTotal) * plotHeight;

  const yTicks = [0, maxTotal / 2, maxTotal];
  const hovered = hoverIndex != null ? data[hoverIndex] : null;

  return (
    <div className="relative">
      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="w-full" role="img" aria-label="Weekly training load by sport">
        <g transform={`translate(${PAD_LEFT}, ${PAD_TOP})`}>
          {yTicks.map((tick) => (
            <g key={tick}>
              <line
                x1={0}
                x2={plotWidth}
                y1={yScale(tick)}
                y2={yScale(tick)}
                stroke="var(--chart-grid)"
                strokeWidth={1}
              />
              <text
                x={-8}
                y={yScale(tick)}
                textAnchor="end"
                dominantBaseline="middle"
                fontSize={11}
                fill="var(--chart-text-secondary)"
              >
                {Math.round(tick).toLocaleString()}
              </text>
            </g>
          ))}

          {data.map((week, i) => {
            const cx = i * bandWidth + bandWidth / 2;
            let cumulative = 0;
            const nonZeroSports = SPORTS.filter((s) => week.by_sport[s].load > 0);

            return (
              <g key={week.week_start}>
                {/* Hover hit target covers the full column band */}
                <rect
                  x={i * bandWidth}
                  y={0}
                  width={bandWidth}
                  height={plotHeight}
                  fill="transparent"
                  onMouseEnter={() => setHoverIndex(i)}
                  onMouseLeave={() => setHoverIndex(null)}
                />

                {SPORTS.map((sport) => {
                  const load = week.by_sport[sport].load;
                  if (load <= 0) return null;
                  const isTop = sport === nonZeroSports[nonZeroSports.length - 1];
                  const segHeight = Math.max((load / maxTotal) * plotHeight - SEGMENT_GAP, 0);
                  const y = yScale(cumulative + load);
                  cumulative += load;

                  return (
                    <rect
                      key={sport}
                      x={cx - barWidth / 2}
                      y={y}
                      width={barWidth}
                      height={segHeight}
                      fill={COLOR_VAR[sport]}
                      rx={isTop ? 4 : 0}
                      opacity={hoverIndex == null || hoverIndex === i ? 1 : 0.35}
                      style={{ transition: "opacity 120ms ease" }}
                    />
                  );
                })}

                <text
                  x={cx}
                  y={plotHeight + 18}
                  textAnchor="middle"
                  fontSize={11}
                  fill="var(--chart-text-secondary)"
                >
                  {formatWeekLabel(week.week_start)}
                </text>
              </g>
            );
          })}
        </g>
      </svg>

      {/* Legend */}
      <div className="mt-1 flex items-center gap-4">
        {SPORTS.map((sport) => (
          <div key={sport} className="flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-400">
            <span
              className="inline-block h-2.5 w-2.5 rounded-sm"
              style={{ backgroundColor: COLOR_VAR[sport] }}
            />
            {sport}
          </div>
        ))}
      </div>

      {hovered && (
        <div className="pointer-events-none absolute right-2 top-2 rounded-md border border-slate-200 bg-white px-3 py-2 text-xs shadow-md dark:border-slate-700 dark:bg-slate-800">
          <div className="font-medium text-slate-900 dark:text-slate-50">{formatWeekLabel(hovered.week_start)}</div>
          {SPORTS.map((sport) => (
            <div key={sport} className="mt-0.5 flex items-center gap-1.5 text-slate-600 dark:text-slate-300">
              <span className="inline-block h-2 w-2 rounded-sm" style={{ backgroundColor: COLOR_VAR[sport] }} />
              {sport}: {Math.round(hovered.by_sport[sport].load).toLocaleString()} ({hovered.by_sport[sport].sessions})
            </div>
          ))}
          <div className="mt-1 border-t border-slate-100 pt-1 font-medium text-slate-900 dark:border-slate-700 dark:text-slate-50">
            Total: {Math.round(hovered.total_load).toLocaleString()}
          </div>
        </div>
      )}
    </div>
  );
}

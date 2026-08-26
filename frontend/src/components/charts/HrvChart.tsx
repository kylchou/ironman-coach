"use client";

import { useState } from "react";
import type { HrvPoint } from "@/lib/api";
import { formatWeekLabel } from "@/lib/format";

// Status roles (good/warning/critical), not series identity -- same palette
// used for the readiness label chip. Shipped with a legend (icon + label),
// never color alone, per the dataviz skill's status-color rule.
const STATUS_STYLE: Record<string, { fill: string; label: string }> = {
  BALANCED: { fill: "#0ca30c", label: "Balanced" },
  UNBALANCED: { fill: "#fab219", label: "Unbalanced" },
  LOW: { fill: "#d03b3b", label: "Low" },
};
const UNKNOWN_STYLE = { fill: "#94a3b8", label: "Unknown" };

const WIDTH = 340;
const HEIGHT = 200;
const PAD_LEFT = 36;
const PAD_RIGHT = 8;
const PAD_TOP = 10;
const PAD_BOTTOM = 24;
const BAR_MAX_WIDTH = 18;

function niceStep(roughStep: number): number {
  if (roughStep <= 0) return 1;
  const magnitude = 10 ** Math.floor(Math.log10(roughStep));
  const normalized = roughStep / magnitude;
  const step = normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 5 ? 5 : 10;
  return step * magnitude;
}

export function HrvChart({ data }: { data: HrvPoint[] }) {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  if (data.length === 0) {
    return <p className="text-xs text-slate-400 dark:text-slate-500">No HRV data for this range.</p>;
  }

  const latest = data[data.length - 1];
  const values = data.map((d) => d.value);
  const bandLow = latest.baseline_low ?? Math.min(...values);
  const bandHigh = latest.baseline_high ?? Math.max(...values);

  const rawMin = Math.min(...values, bandLow);
  const rawMax = Math.max(...values, bandHigh);
  const step = niceStep((rawMax - rawMin) / 4 || 1);
  const yMin = Math.max(0, Math.floor(rawMin / step) * step - step);
  const yMax = Math.ceil(rawMax / step) * step + step;

  const plotWidth = WIDTH - PAD_LEFT - PAD_RIGHT;
  const plotHeight = HEIGHT - PAD_TOP - PAD_BOTTOM;
  const bandWidth = plotWidth / data.length;
  const barWidth = Math.min(BAR_MAX_WIDTH, bandWidth * 0.6);
  const yScale = (v: number) => plotHeight - ((v - yMin) / (yMax - yMin)) * plotHeight;

  const yTicks = [yMin, (yMin + yMax) / 2, yMax];
  const hovered = hoverIndex != null ? data[hoverIndex] : null;
  const hoveredStyle = hovered ? STATUS_STYLE[hovered.status ?? ""] ?? UNKNOWN_STYLE : null;

  const statusesPresent = Array.from(new Set(data.map((d) => d.status).filter(Boolean))) as string[];

  return (
    <div>
      <div className="relative">
        <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="w-full" role="img" aria-label="Heart-rate variability by day">
          <g transform={`translate(${PAD_LEFT}, ${PAD_TOP})`}>
            {yTicks.map((tick) => (
              <g key={tick}>
                <line x1={0} x2={plotWidth} y1={yScale(tick)} y2={yScale(tick)} stroke="var(--chart-grid)" strokeWidth={1} />
                <text x={-6} y={yScale(tick)} textAnchor="end" dominantBaseline="middle" fontSize={10} fill="var(--chart-text-secondary)">
                  {Math.round(tick)}
                </text>
              </g>
            ))}

            {/* Balanced-range band (this machine's most recent baseline) */}
            <rect
              x={0}
              y={yScale(bandHigh)}
              width={plotWidth}
              height={Math.max(yScale(bandLow) - yScale(bandHigh), 0)}
              fill="var(--chart-run)"
              opacity={0.08}
            />

            {data.map((d, i) => {
              const cx = i * bandWidth + bandWidth / 2;
              const style = STATUS_STYLE[d.status ?? ""] ?? UNKNOWN_STYLE;
              const y = yScale(d.value);
              return (
                <g key={d.date}>
                  <rect
                    x={i * bandWidth}
                    y={0}
                    width={bandWidth}
                    height={plotHeight}
                    fill="transparent"
                    onMouseEnter={() => setHoverIndex(i)}
                    onMouseLeave={() => setHoverIndex(null)}
                  />
                  <rect
                    x={cx - barWidth / 2}
                    y={y}
                    width={barWidth}
                    height={Math.max(plotHeight - y, 0)}
                    fill={style.fill}
                    rx={3}
                    opacity={hoverIndex == null || hoverIndex === i ? 1 : 0.45}
                    style={{ transition: "opacity 120ms ease" }}
                  />
                </g>
              );
            })}

            <text x={0} y={plotHeight + 16} fontSize={10} fill="var(--chart-text-secondary)">
              {formatWeekLabel(data[0].date)}
            </text>
            <text x={plotWidth} y={plotHeight + 16} textAnchor="end" fontSize={10} fill="var(--chart-text-secondary)">
              {formatWeekLabel(data[data.length - 1].date)}
            </text>
          </g>
        </svg>

        {hovered && hoveredStyle && (
          <div className="pointer-events-none absolute right-1 top-0 rounded-md border border-slate-200 bg-white px-2 py-1 text-xs shadow-md dark:border-slate-700 dark:bg-slate-800">
            <div className="font-medium text-slate-900 dark:text-slate-50">{Math.round(hovered.value)} ms</div>
            <div className="text-slate-500 dark:text-slate-400">
              {formatWeekLabel(hovered.date)} · {hoveredStyle.label}
            </div>
          </div>
        )}
      </div>

      <div className="mt-1 flex items-center gap-3">
        {statusesPresent.map((s) => {
          const style = STATUS_STYLE[s] ?? UNKNOWN_STYLE;
          return (
            <div key={s} className="flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-400">
              <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: style.fill }} />
              {style.label}
            </div>
          );
        })}
        <span className="ml-auto text-xs text-slate-400 dark:text-slate-500">
          Shaded band = your balanced range
        </span>
      </div>
    </div>
  );
}

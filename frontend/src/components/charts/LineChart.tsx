"use client";

import { useState } from "react";

export type LinePoint = {
  label: string; // x-axis category (e.g. short date)
  value: number | null;
};

const WIDTH = 340;
const HEIGHT = 160;
const PAD_LEFT = 40;
const PAD_RIGHT = 12;
const PAD_TOP = 10;
const PAD_BOTTOM = 24;

/** A "nice" step size for the given range -- 1/2/5/10 x a power of ten,
 * so ticks land on clean numbers instead of arbitrary padded min/max.
 */
function niceStep(roughStep: number): number {
  if (roughStep <= 0) return 1;
  const magnitude = 10 ** Math.floor(Math.log10(roughStep));
  const normalized = roughStep / magnitude;
  const step = normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 5 ? 5 : 10;
  return step * magnitude;
}

function niceBounds(values: number[]): [number, number] {
  if (values.length === 0) return [0, 1];
  const min = Math.min(...values);
  const max = Math.max(...values);
  if (min === max) return [min - 1, max + 1];

  const padded = (max - min) * 1.2;
  const step = niceStep(padded / 4);
  const mid = (min + max) / 2;
  return [Math.floor((mid - padded / 2) / step) * step, Math.ceil((mid + padded / 2) / step) * step];
}

export function LineChart({
  title,
  subtitle,
  data,
  color,
  formatValue,
}: {
  title: string;
  subtitle?: string;
  data: LinePoint[];
  color: string;
  formatValue: (v: number) => string;
}) {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  const points = data.filter((d) => d.value != null) as { label: string; value: number }[];
  if (points.length === 0) {
    return (
      <div>
        <div className="text-sm font-medium text-slate-500 dark:text-slate-400">{title}</div>
        <p className="mt-2 text-sm text-slate-400 dark:text-slate-500">No data yet.</p>
      </div>
    );
  }

  const plotWidth = WIDTH - PAD_LEFT - PAD_RIGHT;
  const plotHeight = HEIGHT - PAD_TOP - PAD_BOTTOM;
  const [yMin, yMax] = niceBounds(data.map((d) => d.value).filter((v): v is number => v != null));

  const xScale = (i: number) => (data.length === 1 ? plotWidth / 2 : (i / (data.length - 1)) * plotWidth);
  const yScale = (v: number) => plotHeight - ((v - yMin) / (yMax - yMin)) * plotHeight;

  const pathD = data
    .map((d, i) => (d.value == null ? null : `${i === 0 || data[i - 1]?.value == null ? "M" : "L"} ${xScale(i)} ${yScale(d.value)}`))
    .filter(Boolean)
    .join(" ");

  const yTicks = [yMin, (yMin + yMax) / 2, yMax];
  const hovered = hoverIndex != null ? data[hoverIndex] : null;

  return (
    <div>
      <div className="flex items-baseline justify-between">
        <div className="text-sm font-medium text-slate-500 dark:text-slate-400">{title}</div>
        {subtitle && <div className="text-xs text-slate-400 dark:text-slate-500">{subtitle}</div>}
      </div>

      <div className="relative mt-1">
        <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="w-full" role="img" aria-label={title}>
          <g transform={`translate(${PAD_LEFT}, ${PAD_TOP})`}>
            {yTicks.map((tick, i) => (
              <g key={i}>
                <line x1={0} x2={plotWidth} y1={yScale(tick)} y2={yScale(tick)} stroke="var(--chart-grid)" strokeWidth={1} />
                <text x={-6} y={yScale(tick)} textAnchor="end" dominantBaseline="middle" fontSize={10} fill="var(--chart-text-secondary)">
                  {formatValue(tick)}
                </text>
              </g>
            ))}

            <path d={pathD} fill="none" stroke={color} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />

            {data.map(
              (d, i) =>
                d.value != null && (
                  <circle
                    key={i}
                    cx={xScale(i)}
                    cy={yScale(d.value)}
                    r={4}
                    fill={color}
                    stroke="var(--chart-surface)"
                    strokeWidth={2}
                  />
                )
            )}

            {data.map((d, i) => (
              <rect
                key={i}
                x={xScale(i) - plotWidth / data.length / 2}
                y={0}
                width={plotWidth / data.length}
                height={plotHeight}
                fill="transparent"
                onMouseEnter={() => setHoverIndex(i)}
                onMouseLeave={() => setHoverIndex(null)}
              />
            ))}

            {hoverIndex != null && (
              <line
                x1={xScale(hoverIndex)}
                x2={xScale(hoverIndex)}
                y1={0}
                y2={plotHeight}
                stroke="var(--chart-text-secondary)"
                strokeWidth={1}
                strokeDasharray="2,2"
              />
            )}

            <text x={0} y={plotHeight + 16} fontSize={10} fill="var(--chart-text-secondary)">
              {data[0]?.label}
            </text>
            <text x={plotWidth} y={plotHeight + 16} textAnchor="end" fontSize={10} fill="var(--chart-text-secondary)">
              {data[data.length - 1]?.label}
            </text>
          </g>
        </svg>

        {hovered && hovered.value != null && (
          <div className="pointer-events-none absolute right-1 top-0 rounded-md border border-slate-200 bg-white px-2 py-1 text-xs shadow-md dark:border-slate-700 dark:bg-slate-800">
            <div className="font-medium text-slate-900 dark:text-slate-50">{formatValue(hovered.value)}</div>
            <div className="text-slate-500 dark:text-slate-400">{hovered.label}</div>
          </div>
        )}
      </div>
    </div>
  );
}

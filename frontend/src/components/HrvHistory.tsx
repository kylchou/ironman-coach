"use client";

import { useState } from "react";
import { fetchHrvHistory, type HrvPoint } from "@/lib/api";
import { HrvChart } from "@/components/charts/HrvChart";

const RANGES = [
  { label: "This week", days: 7 },
  { label: "Last 4 weeks", days: 28 },
] as const;

export function HrvHistory() {
  const [open, setOpen] = useState(false);
  const [days, setDays] = useState<number>(7);
  const [points, setPoints] = useState<HrvPoint[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load(nextDays: number) {
    setDays(nextDays);
    setLoading(true);
    setError(null);
    try {
      setPoints(await fetchHrvHistory(nextDays));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error.");
    } finally {
      setLoading(false);
    }
  }

  function toggle() {
    const next = !open;
    setOpen(next);
    if (next && points === null) {
      load(days);
    }
  }

  return (
    <div className="mt-2">
      <button
        onClick={toggle}
        className="flex items-center gap-1 text-xs font-medium text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
      >
        <span className={`inline-block transition-transform ${open ? "rotate-90" : ""}`}>▸</span>
        HRV history
      </button>

      {open && (
        <div className="mt-2 rounded-md border border-slate-100 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-800/50">
          <div className="flex gap-1 rounded-md bg-white p-0.5 dark:bg-slate-900">
            {RANGES.map((r) => (
              <button
                key={r.days}
                onClick={() => load(r.days)}
                className={`flex-1 rounded px-2 py-1 text-xs font-medium transition-colors ${
                  days === r.days
                    ? "bg-slate-900 text-white dark:bg-slate-50 dark:text-slate-900"
                    : "text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-100"
                }`}
              >
                {r.label}
              </button>
            ))}
          </div>

          <div className="mt-3">
            {loading && <p className="py-2 text-xs text-slate-400 dark:text-slate-500">Loading…</p>}
            {error && <p className="py-2 text-xs text-rose-600 dark:text-rose-400">{error}</p>}
            {!loading && !error && points && <HrvChart data={points} />}
          </div>
        </div>
      )}
    </div>
  );
}

"use client";

import { useState } from "react";
import { CLIENT_API_BASE_URL, type CoachBrief } from "@/lib/api";

export function CoachCard() {
  const [state, setState] = useState<"idle" | "loading" | "error">("idle");
  const [brief, setBrief] = useState<CoachBrief | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function getBrief() {
    setState("loading");
    setError(null);
    try {
      const res = await fetch(`${CLIENT_API_BASE_URL}/coach/brief`, { method: "POST" });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail ?? `${res.status} ${res.statusText}`);
      }
      const data: CoachBrief = await res.json();
      setBrief(data);
      setState("idle");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error.");
      setState("error");
    }
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-50">AI Coach</h3>
        <button
          onClick={getBrief}
          disabled={state === "loading"}
          className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-50 dark:bg-slate-50 dark:text-slate-900"
        >
          {state === "loading" ? "Thinking…" : brief ? "Refresh" : "Get today's brief"}
        </button>
      </div>

      {error && (
        <p className="mt-3 text-sm text-rose-600 dark:text-rose-400">
          {error}
        </p>
      )}

      {!brief && !error && (
        <p className="mt-3 text-sm text-slate-400 dark:text-slate-500">
          Explains your readiness and suggests what to do the next few days, factoring in your
          training, recovery, schedule, and the weather.
        </p>
      )}

      {brief && (
        <div className="mt-3 whitespace-pre-line text-sm leading-relaxed text-slate-700 dark:text-slate-300">
          {brief.brief}
        </div>
      )}
    </div>
  );
}

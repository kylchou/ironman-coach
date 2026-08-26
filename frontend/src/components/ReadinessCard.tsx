import type { Readiness } from "@/lib/api";

// Status roles reserved for state, never reused for series identity. Not
// every label gets a color -- "Ready" is the normal/expected state and
// stays neutral ink; color calls out when something is notably good or
// needs attention, not "everything is fine, proceed as normal".
const LABEL_STYLE: Record<string, { dot: string; chip: string }> = {
  Primed: { dot: "bg-[#0ca30c]", chip: "bg-[#0ca30c]/10 text-[#0ca30c] dark:text-[#3fd23f]" },
  Ready: { dot: "bg-slate-400 dark:bg-slate-500", chip: "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300" },
  "Manage fatigue": { dot: "bg-[#fab219]", chip: "bg-[#fab219]/15 text-[#8a5c00] dark:text-[#fab219]" },
  Recover: { dot: "bg-[#d03b3b]", chip: "bg-[#d03b3b]/10 text-[#d03b3b] dark:text-[#ec8585]" },
};

function ComponentRow({
  label,
  detail,
  score,
}: {
  label: string;
  detail: string;
  score: number | null;
}) {
  return (
    <div className="flex items-center justify-between py-1.5 text-sm">
      <div>
        <span className="font-medium text-slate-700 dark:text-slate-200">{label}</span>
        <span className="ml-2 text-slate-500 dark:text-slate-400">{detail}</span>
      </div>
      <span className="tabular-nums text-slate-400 dark:text-slate-500">
        {score != null ? Math.round(score) : "—"}
      </span>
    </div>
  );
}

export function ReadinessCard({ readiness }: { readiness: Readiness }) {
  const style = LABEL_STYLE[readiness.label] ?? LABEL_STYLE.Ready;
  const { tsb, hrv, sleep, resting_hr } = readiness.components;

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <div className="flex items-baseline gap-4">
        <div className="text-5xl font-semibold tabular-nums text-slate-900 dark:text-slate-50">
          {Math.round(readiness.score)}
        </div>
        <div>
          <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-sm font-medium ${style.chip}`}>
            <span className={`h-2 w-2 rounded-full ${style.dot}`} />
            {readiness.label}
          </span>
          <div className="mt-1 text-xs text-slate-400 dark:text-slate-500">Today&apos;s readiness</div>
        </div>
      </div>

      <div className="mt-4 divide-y divide-slate-100 border-t border-slate-100 dark:divide-slate-800 dark:border-slate-800">
        <ComponentRow
          label="Form"
          detail={`TSB ${tsb.value.toFixed(1)} (${readiness.form_label})`}
          score={tsb.score}
        />
        <ComponentRow
          label="HRV"
          detail={hrv.status ? hrv.status.charAt(0) + hrv.status.slice(1).toLowerCase() : "No data"}
          score={hrv.score}
        />
        <ComponentRow
          label="Sleep"
          detail={sleep.value != null ? `${sleep.value} (${sleep.qualifier?.toLowerCase() ?? ""})` : "No data"}
          score={sleep.score}
        />
        <ComponentRow
          label="Resting HR"
          detail={
            resting_hr.value != null && resting_hr.baseline != null
              ? `${Math.round(resting_hr.value)} bpm (baseline ${Math.round(resting_hr.baseline)})`
              : "No data"
          }
          score={resting_hr.score}
        />
      </div>

      <p className="mt-3 text-xs text-slate-400 dark:text-slate-500">
        Fitness (CTL) {readiness.fitness_ctl.toFixed(1)} · Fatigue (ATL) {readiness.fatigue_atl.toFixed(1)} — a
        heuristic blend, not a medical score.
      </p>
    </div>
  );
}

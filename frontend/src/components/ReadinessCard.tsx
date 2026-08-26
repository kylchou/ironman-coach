import type { Readiness } from "@/lib/api";
import { formatHoursMinutes } from "@/lib/format";
import { RestingHrHistory } from "@/components/RestingHrHistory";

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
  caption,
  children,
}: {
  label: string;
  detail: string;
  score: number | null;
  caption?: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="py-2.5 text-sm">
      <div className="flex items-center justify-between">
        <div>
          <span className="font-medium text-slate-700 dark:text-slate-200">{label}</span>
          <span className="ml-2 text-slate-500 dark:text-slate-400">{detail}</span>
        </div>
        <span className="tabular-nums text-slate-400 dark:text-slate-500">
          {score != null ? Math.round(score) : "—"}
        </span>
      </div>
      {caption && <p className="mt-0.5 text-xs text-slate-400 dark:text-slate-500">{caption}</p>}
      {children}
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
          detail={`${tsb.value >= 0 ? "+" : ""}${tsb.value.toFixed(1)} → ${readiness.form_label}`}
          score={tsb.score}
          caption={
            `Fitness (CTL) ${readiness.fitness_ctl.toFixed(1)} — your average training load over the last ` +
            `42 days. Fatigue (ATL) ${readiness.fatigue_atl.toFixed(1)} — the same, over just the last 7 days. ` +
            `Form (TSB) is Fitness minus Fatigue: positive means you're fresher than your recent training ` +
            `would suggest, negative means you're carrying more fatigue than usual.`
          }
        />

        <ComponentRow
          label="HRV"
          detail={hrv.status ? hrv.status.charAt(0) + hrv.status.slice(1).toLowerCase() : "No data"}
          score={hrv.score}
          caption="Garmin's read on last night's heart-rate variability against your personal baseline range."
        />

        <ComponentRow
          label="Sleep"
          detail={
            sleep.value != null
              ? `${sleep.value}/100 (${sleep.qualifier?.toLowerCase() ?? ""}) — ${formatHoursMinutes(sleep.total_sleep_seconds)} total`
              : "No data"
          }
          score={sleep.score}
        >
          {sleep.value != null && (
            <div className="mt-2 grid grid-cols-4 gap-2 rounded-md bg-slate-50 p-2 dark:bg-slate-800/50">
              {[
                ["Deep", sleep.deep_sleep_seconds],
                ["Light", sleep.light_sleep_seconds],
                ["REM", sleep.rem_sleep_seconds],
                ["Awake", sleep.awake_seconds],
              ].map(([label, seconds]) => (
                <div key={label as string} className="text-center">
                  <div className="text-xs text-slate-400 dark:text-slate-500">{label}</div>
                  <div className="text-xs font-medium tabular-nums text-slate-700 dark:text-slate-200">
                    {formatHoursMinutes(seconds as number | null)}
                  </div>
                </div>
              ))}
            </div>
          )}
          {sleep.value != null && (
            <p className="mt-1.5 text-xs text-slate-400 dark:text-slate-500">
              {sleep.average_heartrate != null && `Avg HR ${Math.round(sleep.average_heartrate)} bpm`}
              {sleep.average_respiration != null && ` · Respiration ${sleep.average_respiration.toFixed(1)} brpm`}
              {sleep.average_spo2 != null && ` · SpO2 ${Math.round(sleep.average_spo2)}%`}
              {sleep.average_stress != null && ` · Stress ${Math.round(sleep.average_stress)}`}
              {sleep.awake_count != null && ` · Woke ${sleep.awake_count}x`}
            </p>
          )}
        </ComponentRow>

        <ComponentRow
          label="Resting HR"
          detail={
            resting_hr.value != null && resting_hr.baseline != null
              ? `${Math.round(resting_hr.value)} bpm vs ${resting_hr.baseline_days}-day baseline ${Math.round(resting_hr.baseline)}`
              : "No data"
          }
          score={resting_hr.score}
          caption={
            resting_hr.baseline != null
              ? `Baseline is your average resting HR over the ${resting_hr.baseline_days} days before today. Meaningfully elevated resting HR can signal illness, stress, or under-recovery.`
              : undefined
          }
        >
          <RestingHrHistory />
        </ComponentRow>
      </div>
    </div>
  );
}

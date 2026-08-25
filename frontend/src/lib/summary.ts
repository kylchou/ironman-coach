import type { Activity } from "./api";

export type SportSummary = {
  sportType: string;
  count: number;
  totalDistanceM: number;
  totalTimeS: number;
};

/** Groups activities by sport_type and totals distance/time, restricted to
 * the last `days` days. Used for the top summary cards.
 */
export function summarizeBySport(activities: Activity[], days: number): SportSummary[] {
  const cutoff = Date.now() - days * 24 * 60 * 60 * 1000;
  const bySport = new Map<string, SportSummary>();

  for (const a of activities) {
    if (new Date(a.start_date).getTime() < cutoff) continue;

    const existing = bySport.get(a.sport_type) ?? {
      sportType: a.sport_type,
      count: 0,
      totalDistanceM: 0,
      totalTimeS: 0,
    };
    existing.count += 1;
    existing.totalDistanceM += a.distance_m ?? 0;
    existing.totalTimeS += a.moving_time_s ?? 0;
    bySport.set(a.sport_type, existing);
  }

  return Array.from(bySport.values()).sort((a, b) => b.totalTimeS - a.totalTimeS);
}

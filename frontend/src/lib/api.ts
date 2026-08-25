export type Activity = {
  id: number;
  source: string;
  external_id: number;
  name: string | null;
  sport_type: string;
  start_date: string;
  distance_m: number | null;
  moving_time_s: number | null;
  elapsed_time_s: number | null;
  total_elevation_gain_m: number | null;
  average_speed_mps: number | null;
  max_speed_mps: number | null;
  average_heartrate: number | null;
  max_heartrate: number | null;
  average_cadence: number | null;
  calories: number | null;
};

const API_BASE_URL = process.env.API_BASE_URL ?? "http://localhost:8000";

/** Fetches from the FastAPI backend. Runs server-side (this is only called
 * from Server Components), so there's no browser CORS involved and no
 * secrets are exposed to the client bundle.
 */
export async function fetchActivities(opts: { sportType?: string; limit?: number } = {}): Promise<Activity[]> {
  const params = new URLSearchParams();
  if (opts.sportType) params.set("sport_type", opts.sportType);
  params.set("limit", String(opts.limit ?? 200));

  const res = await fetch(`${API_BASE_URL}/activities?${params.toString()}`, {
    cache: "no-store",
  });

  if (!res.ok) {
    throw new Error(`Failed to fetch activities: ${res.status} ${await res.text()}`);
  }
  return res.json();
}

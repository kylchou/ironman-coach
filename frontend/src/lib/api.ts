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

export type DailyWeather = {
  date: string;
  temp_max_f: number | null;
  temp_min_f: number | null;
  precipitation_in: number | null;
  wind_speed_max_mph: number | null;
  weather_code: number | null;
  conditions: string;
};

export type WeatherNow = {
  latitude: number;
  longitude: number;
  current: {
    temperature_f: number | null;
    conditions: string;
    weather_code: number | null;
    wind_speed_mph: number | null;
    relative_humidity_pct: number | null;
  };
  daily_forecast: DailyWeather[];
};

export type CalendarEvent = {
  id: string;
  summary: string;
  start: string;
  end: string;
  all_day: boolean;
};

export type SportLoad = {
  load: number;
  distance_m: number;
  time_s: number;
  sessions: number;
};

export type WeeklyLoad = {
  week_start: string;
  by_sport: Record<"Run" | "Ride" | "Swim", SportLoad>;
  total_load: number;
};

export type TrendPoint = {
  week_start: string;
  avg_speed_mps: number | null;
  avg_heartrate: number | null;
  distance_m: number;
  sessions: number;
};

export type Readiness = {
  date: string;
  score: number;
  label: string;
  fitness_ctl: number;
  fatigue_atl: number;
  form_tsb: number;
  form_label: string;
  components: {
    tsb: { value: number; score: number }; // always present -- we compute this ourselves
    hrv: { status: string | null; score: number | null };
    sleep: { value: number | null; qualifier: string | null; score: number | null };
    resting_hr: { value: number | null; baseline: number | null; score: number | null };
  };
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

export async function fetchCurrentWeather(): Promise<WeatherNow> {
  const res = await fetch(`${API_BASE_URL}/weather/current`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Failed to fetch weather: ${res.status} ${await res.text()}`);
  }
  return res.json();
}

export async function fetchUpcomingEvents(days = 7): Promise<CalendarEvent[]> {
  const res = await fetch(`${API_BASE_URL}/calendar/events?days=${days}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Failed to fetch calendar: ${res.status} ${await res.text()}`);
  }
  return res.json();
}

export async function fetchReadiness(): Promise<Readiness> {
  const res = await fetch(`${API_BASE_URL}/readiness/today`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Failed to fetch readiness: ${res.status} ${await res.text()}`);
  }
  return res.json();
}

export async function fetchWeeklyLoad(weeks = 12): Promise<WeeklyLoad[]> {
  const res = await fetch(`${API_BASE_URL}/analytics/weekly-load?weeks=${weeks}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Failed to fetch weekly load: ${res.status} ${await res.text()}`);
  }
  return res.json();
}

export async function fetchTrends(sport: "Run" | "Ride" | "Swim", weeks = 12): Promise<TrendPoint[]> {
  const res = await fetch(`${API_BASE_URL}/analytics/trends?sport=${sport}&weeks=${weeks}`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch trends: ${res.status} ${await res.text()}`);
  }
  return res.json();
}

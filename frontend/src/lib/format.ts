/** Formats seconds as H:MM:SS, or M:SS if under an hour. */
export function formatDuration(seconds: number | null): string {
  if (seconds == null) return "—";
  const s = Math.round(seconds);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  if (h > 0) return `${h}:${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
  return `${m}:${String(sec).padStart(2, "0")}`;
}

export function formatDistance(meters: number | null, sportType: string): string {
  if (meters == null) return "—";
  if (sportType === "Swim") return `${Math.round(meters)} m`;
  return `${(meters / 1000).toFixed(2)} km`;
}

/** Pace/speed, using the convention each sport is normally read in:
 * min/km for running, km/h for cycling, min/100m for swimming.
 */
export function formatPace(mps: number | null, sportType: string): string {
  if (mps == null || mps <= 0) return "—";

  if (sportType === "Ride") {
    return `${(mps * 3.6).toFixed(1)} km/h`;
  }
  if (sportType === "Swim") {
    const secPer100m = 100 / mps;
    const m = Math.floor(secPer100m / 60);
    const s = Math.round(secPer100m % 60);
    return `${m}:${String(s).padStart(2, "0")} /100m`;
  }
  // Run and everything else: min/km
  const secPerKm = 1000 / mps;
  const m = Math.floor(secPerKm / 60);
  const s = Math.round(secPerKm % 60);
  return `${m}:${String(s).padStart(2, "0")} /km`;
}

/** Small visual glyph for a WMO weather code -- see backend's weather_client.py
 * for the authoritative code -> text mapping this loosely mirrors.
 */
export function weatherEmoji(code: number | null): string {
  if (code == null) return "❓";
  if (code === 0 || code === 1) return "☀️";
  if (code === 2) return "⛅";
  if (code === 3) return "☁️";
  if (code === 45 || code === 48) return "🌫️";
  if ([51, 53, 55, 56, 57].includes(code)) return "🌦️";
  if ([61, 63, 65, 66, 67, 80, 81, 82].includes(code)) return "🌧️";
  if ([71, 73, 75, 77, 85, 86].includes(code)) return "❄️";
  if ([95, 96, 99].includes(code)) return "⛈️";
  return "❓";
}

export function formatShortDate(iso: string): string {
  return new Date(`${iso}T12:00:00`).toLocaleDateString(undefined, { weekday: "short" });
}

/** "Jun 29" style label for a week-start date. formatShortDate (weekday-only)
 * is wrong for these -- every week_start is a Monday, so it'd print "Mon"
 * for every single point.
 */
export function formatWeekLabel(iso: string): string {
  return new Date(`${iso}T12:00:00`).toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

/** Converts avg_speed_mps into the unit each sport is normally read in, for
 * charting: seconds/km for running, km/h for cycling, seconds/100m for
 * swimming. Mirrors formatPace's convention but returns a plain number
 * (chart axes need to do math on it), not a formatted string.
 */
export function paceOrSpeedValue(mps: number | null, sportType: string): number | null {
  if (mps == null || mps <= 0) return null;
  if (sportType === "Ride") return mps * 3.6;
  if (sportType === "Swim") return 100 / mps;
  return 1000 / mps;
}

export function paceOrSpeedAxisLabel(sportType: string): string {
  if (sportType === "Ride") return "Speed (km/h)";
  if (sportType === "Swim") return "Pace (min:sec / 100m, lower = faster)";
  return "Pace (min:sec / km, lower = faster)";
}

export function formatPaceOrSpeedValue(value: number, sportType: string): string {
  if (sportType === "Ride") return `${value.toFixed(1)} km/h`;
  const m = Math.floor(value / 60);
  const s = Math.round(value % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

/** "6h 28m" style duration, for sleep stage breakdowns. */
export function formatHoursMinutes(seconds: number | null): string {
  if (seconds == null) return "—";
  const h = Math.floor(seconds / 3600);
  const m = Math.round((seconds % 3600) / 60);
  if (h === 0) return `${m}m`;
  return `${h}h ${m}m`;
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

/** Same output as formatDate, but for a BARE "YYYY-MM-DD" string (no time/
 * offset) -- e.g. resting-HR history dates. Bare date strings parse as UTC
 * midnight per spec; formatDate would then render in the browser's local
 * timezone and silently print the previous day west of UTC. Anchor to noon
 * first, same fix as formatWeekLabel/formatShortDate use.
 */
export function formatBareDate(isoDate: string): string {
  return new Date(`${isoDate}T12:00:00`).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

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

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

import { formatShortDate, weatherEmoji } from "@/lib/format";
import type { WeatherNow } from "@/lib/api";

export function WeatherCard({ weather }: { weather: WeatherNow }) {
  const { current, daily_forecast } = weather;

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-sm font-medium text-slate-500 dark:text-slate-400">
            Weather at training location
          </div>
          <div className="mt-1 flex items-center gap-2">
            <span className="text-3xl">{weatherEmoji(current.weather_code)}</span>
            <span className="text-2xl font-semibold text-slate-900 dark:text-slate-50">
              {current.temperature_f != null ? `${Math.round(current.temperature_f)}°F` : "—"}
            </span>
            <span className="text-sm text-slate-500 dark:text-slate-400">{current.conditions}</span>
          </div>
          <div className="mt-1 text-xs text-slate-400 dark:text-slate-500">
            {current.wind_speed_mph != null && `Wind ${Math.round(current.wind_speed_mph)} mph`}
            {current.relative_humidity_pct != null && ` · Humidity ${Math.round(current.relative_humidity_pct)}%`}
          </div>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-7 gap-2 text-center">
        {daily_forecast.map((day) => (
          <div key={day.date} className="rounded-md bg-slate-50 px-1 py-2 dark:bg-slate-800">
            <div className="text-xs font-medium text-slate-500 dark:text-slate-400">
              {formatShortDate(day.date)}
            </div>
            <div className="mt-1 text-lg">{weatherEmoji(day.weather_code)}</div>
            <div className="mt-1 text-xs text-slate-700 dark:text-slate-300">
              {day.temp_max_f != null ? Math.round(day.temp_max_f) : "—"}°
            </div>
            <div className="text-xs text-slate-400 dark:text-slate-500">
              {day.temp_min_f != null ? Math.round(day.temp_min_f) : "—"}°
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

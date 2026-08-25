import type { CalendarEvent } from "@/lib/api";

function formatEventTime(event: CalendarEvent): string {
  if (event.all_day) {
    return new Date(`${event.start}T12:00:00`).toLocaleDateString(undefined, {
      weekday: "short",
      month: "short",
      day: "numeric",
    });
  }
  const start = new Date(event.start);
  return start.toLocaleString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function UpcomingEvents({ events }: { events: CalendarEvent[] }) {
  if (events.length === 0) {
    return (
      <p className="text-sm text-slate-500 dark:text-slate-400">
        Nothing on the calendar for the next week.
      </p>
    );
  }

  return (
    <ul className="divide-y divide-slate-100 dark:divide-slate-800">
      {events.map((event) => (
        <li key={event.id} className="flex items-center justify-between gap-4 py-2 text-sm">
          <span className="font-medium text-slate-900 dark:text-slate-50">{event.summary}</span>
          <span className="whitespace-nowrap text-slate-500 dark:text-slate-400">
            {formatEventTime(event)}
          </span>
        </li>
      ))}
    </ul>
  );
}

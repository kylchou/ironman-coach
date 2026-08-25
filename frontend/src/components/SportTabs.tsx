import Link from "next/link";

const SPORTS = ["All", "Run", "Ride", "Swim"];

export function SportTabs({ active }: { active: string }) {
  return (
    <div className="flex gap-1 rounded-lg bg-slate-100 p-1 dark:bg-slate-800 w-fit">
      {SPORTS.map((sport) => {
        const isActive = sport === active;
        const href = sport === "All" ? "/" : `/?sport=${sport}`;
        return (
          <Link
            key={sport}
            href={href}
            className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
              isActive
                ? "bg-white text-slate-900 shadow-sm dark:bg-slate-900 dark:text-slate-50"
                : "text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
            }`}
          >
            {sport}
          </Link>
        );
      })}
    </div>
  );
}

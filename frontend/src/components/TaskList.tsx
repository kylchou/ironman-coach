"use client";

import { useState } from "react";
import { createTask, deleteTask, fetchTasks, syncCanvasTasks, updateTask, type Task } from "@/lib/api";
import { formatDate } from "@/lib/format";

function sortTasks(tasks: Task[]): Task[] {
  return [...tasks].sort((a, b) => {
    // Completed sinks to the bottom regardless of due date -- otherwise a
    // completed task due tomorrow would outrank an incomplete one due next
    // week, which reads as broken, not "sorted by due date".
    if (a.completed !== b.completed) return a.completed ? 1 : -1;
    if (a.due_date == null && b.due_date == null) return 0;
    if (a.due_date == null) return 1; // no-due-date tasks sort last within their group
    if (b.due_date == null) return -1;
    return new Date(a.due_date).getTime() - new Date(b.due_date).getTime();
  });
}

function isOverdue(task: Task): boolean {
  return !task.completed && task.due_date != null && new Date(task.due_date).getTime() < Date.now();
}

export function TaskList({ initialTasks }: { initialTasks: Task[] }) {
  const [tasks, setTasks] = useState<Task[]>(sortTasks(initialTasks));
  const [title, setTitle] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [adding, setAdding] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    // include_completed=true -- completed tasks stay visible (struck
    // through, via the `completed` styling below) rather than vanishing
    // the instant you check them off.
    setTasks(sortTasks(await fetchTasks(true)));
  }

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;
    setAdding(true);
    setError(null);
    try {
      const iso = dueDate ? new Date(`${dueDate}T23:59:00`).toISOString() : undefined;
      await createTask(title.trim(), iso);
      setTitle("");
      setDueDate("");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add task.");
    } finally {
      setAdding(false);
    }
  }

  async function handleToggle(task: Task) {
    // Optimistic update -- flip it locally right away, reconcile after.
    setTasks((prev) => prev.map((t) => (t.id === task.id ? { ...t, completed: !t.completed } : t)));
    try {
      await updateTask(task.id, { completed: !task.completed });
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update task.");
      await refresh(); // roll back to server truth
    }
  }

  async function handleDelete(id: number) {
    setTasks((prev) => prev.filter((t) => t.id !== id));
    try {
      await deleteTask(id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete task.");
      await refresh();
    }
  }

  async function handleSyncCanvas() {
    setSyncing(true);
    setError(null);
    try {
      await syncCanvasTasks();
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to sync Canvas.");
    } finally {
      setSyncing(false);
    }
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-50">To-Do</h3>
        <button
          onClick={handleSyncCanvas}
          disabled={syncing}
          className="text-xs font-medium text-slate-500 hover:text-slate-800 disabled:opacity-50 dark:text-slate-400 dark:hover:text-slate-100"
        >
          {syncing ? "Syncing…" : "Sync Canvas"}
        </button>
      </div>

      <form onSubmit={handleAdd} className="mt-3 flex gap-2">
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Add a task…"
          className="flex-1 rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-slate-400 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
        />
        <input
          type="date"
          value={dueDate}
          onChange={(e) => setDueDate(e.target.value)}
          className="rounded-md border border-slate-200 bg-white px-2 py-1.5 text-sm text-slate-700 focus:outline-none focus:ring-1 focus:ring-slate-400 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
        />
        <button
          type="submit"
          disabled={adding || !title.trim()}
          className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-40 dark:bg-slate-50 dark:text-slate-900"
        >
          Add
        </button>
      </form>

      {error && <p className="mt-2 text-xs text-rose-600 dark:text-rose-400">{error}</p>}

      {tasks.length === 0 ? (
        <p className="mt-4 text-sm text-slate-400 dark:text-slate-500">Nothing on your list. Nice.</p>
      ) : (
        <ul className="mt-3 divide-y divide-slate-100 dark:divide-slate-800">
          {tasks.map((task) => (
            <li key={task.id} className="flex items-center gap-3 py-2">
              <input
                type="checkbox"
                checked={task.completed}
                onChange={() => handleToggle(task)}
                className="h-4 w-4 shrink-0 accent-slate-700 dark:accent-slate-300"
              />
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-1.5">
                  <span
                    className={`text-sm ${
                      task.completed
                        ? "text-slate-400 line-through dark:text-slate-600"
                        : "text-slate-800 dark:text-slate-100"
                    }`}
                  >
                    {task.source_url ? (
                      <a href={task.source_url} target="_blank" rel="noreferrer" className="hover:underline">
                        {task.title}
                      </a>
                    ) : (
                      task.title
                    )}
                  </span>
                  {task.source === "canvas" && (
                    <span className="rounded-full bg-violet-100 px-1.5 py-0.5 text-[10px] font-medium text-violet-700 dark:bg-violet-950 dark:text-violet-300">
                      {task.course_name ?? "Canvas"}
                    </span>
                  )}
                </div>
                {task.due_date && (
                  <div
                    className={`text-xs ${
                      isOverdue(task)
                        ? "font-medium text-[#d03b3b] dark:text-[#ec8585]"
                        : "text-slate-400 dark:text-slate-500"
                    }`}
                  >
                    Due {formatDate(task.due_date)}
                    {isOverdue(task) && " · overdue"}
                  </div>
                )}
              </div>
              <button
                onClick={() => handleDelete(task.id)}
                className="shrink-0 text-slate-300 hover:text-slate-600 dark:text-slate-600 dark:hover:text-slate-300"
                aria-label={`Delete ${task.title}`}
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

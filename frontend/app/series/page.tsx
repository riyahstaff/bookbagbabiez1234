"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { createSeries, listSeries } from "@/lib/api";
import { TextField } from "@/components/Field";
import type { Series } from "@/lib/types";

export default function SeriesListPage() {
  const [series, setSeries] = useState<Series[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [genre, setGenre] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function refresh() {
    setLoading(true);
    try {
      setSeries(await listSeries());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load series");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    if (!title.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      await createSeries({ title, genre: genre || null });
      setTitle("");
      setGenre("");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create series");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">Series</h1>
        <p className="text-sm text-slate-500">
          Every project starts here. Pick a series to manage its characters and episodes.
        </p>
      </div>

      {error && <p className="rounded bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

      <form
        onSubmit={handleCreate}
        className="flex flex-wrap items-end gap-3 rounded-lg border border-slate-200 bg-white p-4"
      >
        <TextField
          label="Title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="My Cartoon"
          required
        />
        <TextField
          label="Genre"
          value={genre}
          onChange={(e) => setGenre(e.target.value)}
          placeholder="Comedy"
        />
        <button
          type="submit"
          disabled={submitting}
          className="rounded bg-slate-900 px-4 py-1.5 text-sm font-medium text-white disabled:opacity-50"
        >
          {submitting ? "Creating..." : "Create Series"}
        </button>
      </form>

      {loading ? (
        <p className="text-sm text-slate-500">Loading...</p>
      ) : series.length === 0 ? (
        <p className="text-sm text-slate-500">No series yet. Create your first one above.</p>
      ) : (
        <ul className="divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white">
          {series.map((item) => (
            <li key={item.id} className="flex items-center justify-between px-4 py-3">
              <div>
                <Link href={`/series/${item.id}`} className="font-medium hover:underline">
                  {item.title}
                </Link>
                <p className="text-xs text-slate-500">
                  {item.series_code} · {item.genre || "No genre set"}
                </p>
              </div>
              <Link href={`/series/${item.id}`} className="text-sm text-slate-500 hover:underline">
                Manage →
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

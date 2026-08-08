"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { createEpisode, listEpisodes } from "@/lib/api";
import { TextField } from "@/components/Field";
import type { Episode } from "@/lib/types";

export default function EpisodeListPage() {
  const params = useParams<{ seriesId: string }>();
  const seriesId = Number(params.seriesId);

  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [episodeNumber, setEpisodeNumber] = useState("");
  const [title, setTitle] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function refresh() {
    setLoading(true);
    try {
      setEpisodes(await listEpisodes(seriesId));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load episodes");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [seriesId]);

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    const number = Number(episodeNumber);
    if (!title.trim() || !number) return;
    setSubmitting(true);
    setError(null);
    try {
      await createEpisode(seriesId, { episode_number: number, title });
      setEpisodeNumber("");
      setTitle("");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create episode");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <Link href={`/series/${seriesId}`} className="text-sm text-slate-500 hover:underline">
          ← Back to series
        </Link>
        <h1 className="mt-1 text-2xl font-semibold">Episodes</h1>
      </div>

      {error && <p className="rounded bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

      <form
        onSubmit={handleCreate}
        className="flex flex-wrap items-end gap-3 rounded-lg border border-slate-200 bg-white p-4"
      >
        <TextField
          label="Episode #"
          type="number"
          min={1}
          value={episodeNumber}
          onChange={(e) => setEpisodeNumber(e.target.value)}
          className="w-24"
          required
        />
        <TextField
          label="Title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Pilot"
          required
        />
        <button
          type="submit"
          disabled={submitting}
          className="rounded bg-slate-900 px-4 py-1.5 text-sm font-medium text-white disabled:opacity-50"
        >
          {submitting ? "Creating..." : "Create Episode"}
        </button>
      </form>

      {loading ? (
        <p className="text-sm text-slate-500">Loading...</p>
      ) : episodes.length === 0 ? (
        <p className="text-sm text-slate-500">No episodes yet. Create your first one above.</p>
      ) : (
        <ul className="divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white">
          {episodes.map((episode) => (
            <li key={episode.id} className="flex items-center justify-between px-4 py-3">
              <div>
                <Link
                  href={`/series/${seriesId}/episodes/${episode.id}`}
                  className="font-medium hover:underline"
                >
                  {episode.episode_code}: {episode.title}
                </Link>
                <p className="text-xs text-slate-500">{episode.status}</p>
              </div>
              <Link
                href={`/series/${seriesId}/episodes/${episode.id}`}
                className="text-sm text-slate-500 hover:underline"
              >
                Edit →
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { deleteEpisode, getEpisode, updateEpisode } from "@/lib/api";
import { TextField, TextAreaField, SelectField } from "@/components/Field";
import { EPISODE_STATUSES, type Episode, type EpisodeInput, type EpisodeStatus } from "@/lib/types";

export default function EpisodeDetailPage() {
  const params = useParams<{ seriesId: string; episodeId: string }>();
  const seriesId = Number(params.seriesId);
  const episodeId = Number(params.episodeId);
  const router = useRouter();

  const [episode, setEpisode] = useState<Episode | null>(null);
  const [form, setForm] = useState<EpisodeInput & { status?: EpisodeStatus }>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedAt, setSavedAt] = useState<number | null>(null);

  useEffect(() => {
    getEpisode(episodeId)
      .then((data) => {
        setEpisode(data);
        setForm(data);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load episode"))
      .finally(() => setLoading(false));
  }, [episodeId]);

  function set<K extends keyof (EpisodeInput & { status?: EpisodeStatus })>(
    key: K,
    value: (EpisodeInput & { status?: EpisodeStatus })[K],
  ) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSave(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const updated = await updateEpisode(episodeId, form);
      setEpisode(updated);
      setForm(updated);
      setSavedAt(Date.now());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save episode");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!confirm(`Delete "${episode?.title}"?`)) return;
    try {
      await deleteEpisode(episodeId);
      router.push(`/series/${seriesId}/episodes`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete episode");
    }
  }

  if (loading) return <p className="text-sm text-slate-500">Loading...</p>;
  if (!episode) return <p className="text-sm text-red-700">{error ?? "Episode not found."}</p>;

  return (
    <div className="space-y-8">
      <div className="flex items-start justify-between">
        <div>
          <Link href={`/series/${seriesId}/episodes`} className="text-sm text-slate-500 hover:underline">
            ← Back to episodes
          </Link>
          <p className="mt-1 text-xs font-medium uppercase text-slate-400">{episode.episode_code}</p>
          <h1 className="text-2xl font-semibold">{episode.title}</h1>
        </div>
        <button
          onClick={handleDelete}
          className="rounded border border-red-200 px-3 py-1.5 text-sm text-red-700 hover:bg-red-50"
        >
          Delete Episode
        </button>
      </div>

      {error && <p className="rounded bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
      {savedAt && <p className="rounded bg-green-50 px-3 py-2 text-sm text-green-700">Saved.</p>}

      <form onSubmit={handleSave} className="space-y-4 rounded-lg border border-slate-200 bg-white p-4">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <TextField
            label="Episode #"
            type="number"
            value={form.episode_number ?? episode.episode_number}
            onChange={(e) => set("episode_number", Number(e.target.value))}
          />
          <TextField label="Title" value={form.title ?? ""} onChange={(e) => set("title", e.target.value)} />
          <SelectField
            label="Status"
            value={form.status ?? episode.status}
            onChange={(e) => set("status", e.target.value as EpisodeStatus)}
          >
            {EPISODE_STATUSES.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </SelectField>
          <TextField
            label="Target Runtime (seconds)"
            type="number"
            value={form.target_runtime_seconds ?? ""}
            onChange={(e) => set("target_runtime_seconds", e.target.value ? Number(e.target.value) : null)}
          />
        </div>

        <TextAreaField
          label="Summary"
          rows={2}
          value={form.summary ?? ""}
          onChange={(e) => set("summary", e.target.value)}
        />
        <TextAreaField
          label="Treatment"
          rows={4}
          value={form.treatment ?? ""}
          onChange={(e) => set("treatment", e.target.value)}
          placeholder="Paste the original treatment here - it's preserved as-is and never overwritten by later pipeline stages."
        />
        <TextAreaField
          label="Script"
          rows={6}
          value={form.script ?? ""}
          onChange={(e) => set("script", e.target.value)}
        />
        <TextAreaField
          label="Narration"
          rows={3}
          value={form.narration ?? ""}
          onChange={(e) => set("narration", e.target.value)}
        />

        <button
          type="submit"
          disabled={saving}
          className="rounded bg-slate-900 px-4 py-1.5 text-sm font-medium text-white disabled:opacity-50"
        >
          {saving ? "Saving..." : "Save Changes"}
        </button>
      </form>
    </div>
  );
}

"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { deleteSeries, getSeries, updateSeries } from "@/lib/api";
import { TextField, TextAreaField } from "@/components/Field";
import type { Series, SeriesInput } from "@/lib/types";

export default function SeriesDetailPage() {
  const params = useParams<{ seriesId: string }>();
  const seriesId = Number(params.seriesId);
  const router = useRouter();

  const [series, setSeries] = useState<Series | null>(null);
  const [form, setForm] = useState<SeriesInput>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedAt, setSavedAt] = useState<number | null>(null);

  useEffect(() => {
    getSeries(seriesId)
      .then((data) => {
        setSeries(data);
        setForm(data);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load series"))
      .finally(() => setLoading(false));
  }, [seriesId]);

  function set<K extends keyof SeriesInput>(key: K, value: SeriesInput[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSave(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const updated = await updateSeries(seriesId, form);
      setSeries(updated);
      setForm(updated);
      setSavedAt(Date.now());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save series");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!confirm(`Delete "${series?.title}"? This removes all its characters and episodes.`)) return;
    try {
      await deleteSeries(seriesId);
      router.push("/series");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete series");
    }
  }

  if (loading) return <p className="text-sm text-slate-500">Loading...</p>;
  if (!series) return <p className="text-sm text-red-700">{error ?? "Series not found."}</p>;

  return (
    <div className="space-y-8">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium uppercase text-slate-400">{series.series_code}</p>
          <h1 className="text-2xl font-semibold">{series.title}</h1>
        </div>
        <button
          onClick={handleDelete}
          className="rounded border border-red-200 px-3 py-1.5 text-sm text-red-700 hover:bg-red-50"
        >
          Delete Series
        </button>
      </div>

      <nav className="flex gap-4 border-b border-slate-200 pb-2 text-sm">
        <Link href={`/series/${seriesId}/characters`} className="font-medium text-slate-700 hover:underline">
          Characters →
        </Link>
        <Link href={`/series/${seriesId}/episodes`} className="font-medium text-slate-700 hover:underline">
          Episodes →
        </Link>
      </nav>

      {error && <p className="rounded bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
      {savedAt && <p className="rounded bg-green-50 px-3 py-2 text-sm text-green-700">Saved.</p>}

      <form onSubmit={handleSave} className="space-y-4 rounded-lg border border-slate-200 bg-white p-4">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <TextField label="Title" value={form.title ?? ""} onChange={(e) => set("title", e.target.value)} />
          <TextField label="Genre" value={form.genre ?? ""} onChange={(e) => set("genre", e.target.value)} />
          <TextField
            label="Animation Style"
            value={form.animation_style ?? ""}
            onChange={(e) => set("animation_style", e.target.value)}
          />
          <TextField
            label="Target Resolution"
            value={form.target_resolution ?? ""}
            onChange={(e) => set("target_resolution", e.target.value)}
          />
          <TextField
            label="Default FPS"
            type="number"
            value={form.default_fps ?? 24}
            onChange={(e) => set("default_fps", Number(e.target.value))}
          />
          <TextField
            label="Target Episode Length (minutes)"
            type="number"
            value={form.target_episode_length_minutes ?? 30}
            onChange={(e) => set("target_episode_length_minutes", Number(e.target.value))}
          />
          <TextField
            label="Aspect Ratio"
            value={form.aspect_ratio ?? ""}
            onChange={(e) => set("aspect_ratio", e.target.value)}
          />
          <TextField
            label="Default Video Provider"
            value={form.default_video_provider ?? ""}
            onChange={(e) => set("default_video_provider", e.target.value)}
            placeholder="wan_ti2v_5b"
          />
          <TextField
            label="Default Image Provider"
            value={form.default_image_provider ?? ""}
            onChange={(e) => set("default_image_provider", e.target.value)}
            placeholder="flux_schnell"
          />
        </div>

        <TextAreaField
          label="Description"
          rows={2}
          value={form.description ?? ""}
          onChange={(e) => set("description", e.target.value)}
        />
        <TextAreaField
          label="Visual Style Prompt"
          rows={2}
          value={form.visual_style_prompt ?? ""}
          onChange={(e) => set("visual_style_prompt", e.target.value)}
        />
        <TextAreaField
          label="Negative Style Prompt"
          rows={2}
          value={form.negative_style_prompt ?? ""}
          onChange={(e) => set("negative_style_prompt", e.target.value)}
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

"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  createScene,
  deleteEpisode,
  generateEpisodeOutline,
  generateEpisodeScript,
  generateScenes,
  getEpisode,
  listScenes,
  updateEpisode,
} from "@/lib/api";
import { TextField, TextAreaField, SelectField } from "@/components/Field";
import EpisodeExportPanel from "@/components/EpisodeExportPanel";
import {
  EPISODE_STATUSES,
  type Episode,
  type EpisodeInput,
  type EpisodeStatus,
  type Scene,
} from "@/lib/types";

export default function EpisodeDetailPage() {
  const params = useParams<{ seriesId: string; episodeId: string }>();
  const seriesId = Number(params.seriesId);
  const episodeId = Number(params.episodeId);
  const router = useRouter();

  const [episode, setEpisode] = useState<Episode | null>(null);
  const [form, setForm] = useState<EpisodeInput & { status?: EpisodeStatus }>({});
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedAt, setSavedAt] = useState<number | null>(null);
  const [generating, setGenerating] = useState<"outline" | "script" | "scenes" | null>(null);
  const [newSceneNumber, setNewSceneNumber] = useState("");

  function refreshScenes() {
    listScenes(episodeId).then(setScenes);
  }

  function refreshEpisode() {
    return getEpisode(episodeId).then((data) => {
      setEpisode(data);
      setForm(data);
      return data;
    });
  }

  useEffect(() => {
    refreshEpisode()
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load episode"))
      .finally(() => setLoading(false));
    refreshScenes();
    // eslint-disable-next-line react-hooks/exhaustive-deps
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

  async function handleGenerateOutline() {
    setGenerating("outline");
    setError(null);
    try {
      const updated = await generateEpisodeOutline(episodeId);
      setEpisode(updated);
      setForm(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate outline");
    } finally {
      setGenerating(null);
    }
  }

  async function handleGenerateScript() {
    setGenerating("script");
    setError(null);
    try {
      const updated = await generateEpisodeScript(episodeId);
      setEpisode(updated);
      setForm(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate script");
    } finally {
      setGenerating(null);
    }
  }

  async function handleGenerateScenes() {
    setGenerating("scenes");
    setError(null);
    try {
      await generateScenes(episodeId);
      refreshScenes();
      const updated = await getEpisode(episodeId);
      setEpisode(updated);
      setForm(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate scenes");
    } finally {
      setGenerating(null);
    }
  }

  async function handleAddScene(event: React.FormEvent) {
    event.preventDefault();
    const number = Number(newSceneNumber);
    if (!number) return;
    try {
      await createScene(episodeId, { scene_number: number });
      setNewSceneNumber("");
      refreshScenes();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create scene");
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

        <div className="space-y-1">
          <div className="flex items-center justify-between">
            <label className="text-xs font-medium text-slate-600">Outline</label>
            <button
              type="button"
              onClick={handleGenerateOutline}
              disabled={generating !== null}
              className="rounded border border-slate-300 px-3 py-1 text-xs font-medium hover:bg-slate-50 disabled:opacity-50"
            >
              {generating === "outline" ? "Generating..." : "Generate Outline from Treatment"}
            </button>
          </div>
          <textarea
            rows={4}
            className="w-full rounded border border-slate-300 px-3 py-1.5 text-sm"
            value={form.outline ?? ""}
            onChange={(e) => set("outline", e.target.value)}
          />
        </div>

        <div className="space-y-1">
          <div className="flex items-center justify-between">
            <label className="text-xs font-medium text-slate-600">Script</label>
            <button
              type="button"
              onClick={handleGenerateScript}
              disabled={generating !== null}
              className="rounded border border-slate-300 px-3 py-1 text-xs font-medium hover:bg-slate-50 disabled:opacity-50"
            >
              {generating === "script" ? "Generating..." : "Generate Script from Outline"}
            </button>
          </div>
          <textarea
            rows={8}
            className="w-full rounded border border-slate-300 px-3 py-1.5 text-sm"
            value={form.script ?? ""}
            onChange={(e) => set("script", e.target.value)}
          />
        </div>

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

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-medium">Scenes</h2>
            <p className="text-sm text-slate-500">
              Break the script into scenes with AI, or add one manually - both are always available.
            </p>
          </div>
          <button
            onClick={handleGenerateScenes}
            disabled={generating !== null || scenes.length > 0}
            title={scenes.length > 0 ? "Delete existing scenes first to regenerate" : ""}
            className="rounded bg-slate-900 px-4 py-1.5 text-sm font-medium text-white disabled:opacity-50"
          >
            {generating === "scenes" ? "Generating..." : "Generate Scenes from Script"}
          </button>
        </div>

        <form onSubmit={handleAddScene} className="flex items-end gap-3 rounded-lg border border-slate-200 bg-white p-3">
          <TextField
            label="New Scene #"
            type="number"
            min={1}
            value={newSceneNumber}
            onChange={(e) => setNewSceneNumber(e.target.value)}
            className="w-28"
          />
          <button type="submit" className="rounded border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50">
            Add Scene Manually
          </button>
        </form>

        {scenes.length === 0 ? (
          <p className="text-sm text-slate-500">No scenes yet.</p>
        ) : (
          <ul className="divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white">
            {scenes.map((scene) => (
              <li key={scene.id} className="flex items-center justify-between px-4 py-3">
                <div>
                  <Link
                    href={`/series/${seriesId}/episodes/${episodeId}/scenes/${scene.id}`}
                    className="font-medium hover:underline"
                  >
                    Scene {scene.scene_number}
                  </Link>
                  <p className="text-xs text-slate-500">
                    {scene.status} · {scene.characters.length} character(s)
                    {scene.emotional_tone ? ` · ${scene.emotional_tone}` : ""}
                  </p>
                </div>
                <Link
                  href={`/series/${seriesId}/episodes/${episodeId}/scenes/${scene.id}`}
                  className="text-sm text-slate-500 hover:underline"
                >
                  Edit →
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>

      <EpisodeExportPanel episodeId={episodeId} onEpisodeChanged={refreshEpisode} />
    </div>
  );
}

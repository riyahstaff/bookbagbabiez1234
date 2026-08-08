"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  createShot,
  deleteScene,
  generateShots,
  getScene,
  listCharacters,
  listLocations,
  listShots,
  mediaUrl,
  setSceneCharacters,
  updateScene,
} from "@/lib/api";
import { TextField, TextAreaField, SelectField } from "@/components/Field";
import type { Character, Location, Scene, SceneInput, Shot } from "@/lib/types";

export default function SceneDetailPage() {
  const params = useParams<{ seriesId: string; episodeId: string; sceneId: string }>();
  const seriesId = Number(params.seriesId);
  const episodeId = Number(params.episodeId);
  const sceneId = Number(params.sceneId);
  const router = useRouter();

  const [scene, setScene] = useState<Scene | null>(null);
  const [form, setForm] = useState<SceneInput>({});
  const [characters, setCharacters] = useState<Character[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [selectedCharacterIds, setSelectedCharacterIds] = useState<Set<number>>(new Set());
  const [shots, setShots] = useState<Shot[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedAt, setSavedAt] = useState<number | null>(null);
  const [newShotNumber, setNewShotNumber] = useState("");

  function refreshShots() {
    listShots(sceneId).then(setShots);
  }

  useEffect(() => {
    getScene(sceneId)
      .then((data) => {
        setScene(data);
        setForm(data);
        setSelectedCharacterIds(new Set(data.characters.map((c) => c.character_id)));
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load scene"))
      .finally(() => setLoading(false));
    listCharacters(seriesId).then(setCharacters);
    listLocations(seriesId).then(setLocations);
    refreshShots();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sceneId, seriesId]);

  function set<K extends keyof SceneInput>(key: K, value: SceneInput[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSave(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const updated = await updateScene(sceneId, form);
      setScene(updated);
      setForm(updated);
      setSavedAt(Date.now());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save scene");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!confirm(`Delete Scene ${scene?.scene_number}? This also deletes its shots.`)) return;
    try {
      await deleteScene(sceneId);
      router.push(`/series/${seriesId}/episodes/${episodeId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete scene");
    }
  }

  function toggleCharacter(characterId: number) {
    setSelectedCharacterIds((prev) => {
      const next = new Set(prev);
      if (next.has(characterId)) next.delete(characterId);
      else next.add(characterId);
      return next;
    });
  }

  async function handleSaveCharacters() {
    setError(null);
    try {
      const updated = await setSceneCharacters(
        sceneId,
        Array.from(selectedCharacterIds).map((id) => ({ character_id: id, outfit_id: null })),
      );
      setScene(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save character list");
    }
  }

  async function handleGenerateShots() {
    setGenerating(true);
    setError(null);
    try {
      await generateShots(sceneId);
      refreshShots();
      const updated = await getScene(sceneId);
      setScene(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate shots");
    } finally {
      setGenerating(false);
    }
  }

  async function handleAddShot(event: React.FormEvent) {
    event.preventDefault();
    const number = Number(newShotNumber);
    if (!number) return;
    try {
      await createShot(sceneId, { shot_number: number });
      setNewShotNumber("");
      refreshShots();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create shot");
    }
  }

  if (loading) return <p className="text-sm text-slate-500">Loading...</p>;
  if (!scene) return <p className="text-sm text-red-700">{error ?? "Scene not found."}</p>;

  return (
    <div className="space-y-8">
      <div className="flex items-start justify-between">
        <div>
          <Link
            href={`/series/${seriesId}/episodes/${episodeId}`}
            className="text-sm text-slate-500 hover:underline"
          >
            ← Back to episode
          </Link>
          <h1 className="mt-1 text-2xl font-semibold">Scene {scene.scene_number}</h1>
          <p className="text-xs text-slate-500">{scene.status}</p>
        </div>
        <button
          onClick={handleDelete}
          className="rounded border border-red-200 px-3 py-1.5 text-sm text-red-700 hover:bg-red-50"
        >
          Delete Scene
        </button>
      </div>

      {error && <p className="rounded bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
      {savedAt && <p className="rounded bg-green-50 px-3 py-2 text-sm text-green-700">Saved.</p>}

      <form onSubmit={handleSave} className="space-y-4 rounded-lg border border-slate-200 bg-white p-4">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <TextField
            label="Scene #"
            type="number"
            value={form.scene_number ?? scene.scene_number}
            onChange={(e) => set("scene_number", Number(e.target.value))}
          />
          <SelectField
            label="Location"
            value={form.location_id ?? ""}
            onChange={(e) => set("location_id", e.target.value ? Number(e.target.value) : null)}
          >
            <option value="">Unassigned</option>
            {locations.map((location) => (
              <option key={location.id} value={location.id}>
                {location.name}
              </option>
            ))}
          </SelectField>
          <TextField
            label="Time of Day"
            value={form.time_of_day ?? ""}
            onChange={(e) => set("time_of_day", e.target.value)}
            placeholder="DAY"
          />
          <TextField
            label="Emotional Tone"
            value={form.emotional_tone ?? ""}
            onChange={(e) => set("emotional_tone", e.target.value)}
          />
          <TextField
            label="Estimated Duration (seconds)"
            type="number"
            value={form.estimated_duration_seconds ?? ""}
            onChange={(e) => set("estimated_duration_seconds", e.target.value ? Number(e.target.value) : null)}
          />
        </div>

        <TextAreaField
          label="Action Description"
          rows={3}
          value={form.action_description ?? ""}
          onChange={(e) => set("action_description", e.target.value)}
        />
        <TextAreaField
          label="Dialogue"
          rows={3}
          value={form.dialogue ?? ""}
          onChange={(e) => set("dialogue", e.target.value)}
        />
        <TextAreaField
          label="Narration"
          rows={2}
          value={form.narration ?? ""}
          onChange={(e) => set("narration", e.target.value)}
        />
        <TextAreaField
          label="Continuity Notes"
          rows={2}
          value={form.continuity_notes ?? ""}
          onChange={(e) => set("continuity_notes", e.target.value)}
        />

        <button
          type="submit"
          disabled={saving}
          className="rounded bg-slate-900 px-4 py-1.5 text-sm font-medium text-white disabled:opacity-50"
        >
          {saving ? "Saving..." : "Save Changes"}
        </button>
      </form>

      <section className="space-y-3 rounded-lg border border-slate-200 bg-white p-4">
        <h2 className="text-lg font-medium">Characters Present</h2>
        {characters.length === 0 ? (
          <p className="text-sm text-slate-500">No characters defined in this series yet.</p>
        ) : (
          <div className="flex flex-wrap gap-4">
            {characters.map((character) => (
              <label key={character.id} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={selectedCharacterIds.has(character.id)}
                  onChange={() => toggleCharacter(character.id)}
                  className="h-4 w-4"
                />
                {character.name}
              </label>
            ))}
          </div>
        )}
        <button
          onClick={handleSaveCharacters}
          className="rounded border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50"
        >
          Save Character List
        </button>
      </section>

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-medium">Shots</h2>
            <p className="text-sm text-slate-500">Break this scene into a shot list with AI, or add one manually.</p>
          </div>
          <button
            onClick={handleGenerateShots}
            disabled={generating || shots.length > 0}
            title={shots.length > 0 ? "Delete existing shots first to regenerate" : ""}
            className="rounded bg-slate-900 px-4 py-1.5 text-sm font-medium text-white disabled:opacity-50"
          >
            {generating ? "Generating..." : "Generate Shots from Scene"}
          </button>
        </div>

        <form onSubmit={handleAddShot} className="flex items-end gap-3 rounded-lg border border-slate-200 bg-white p-3">
          <TextField
            label="New Shot #"
            type="number"
            min={1}
            value={newShotNumber}
            onChange={(e) => setNewShotNumber(e.target.value)}
            className="w-28"
          />
          <button type="submit" className="rounded border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50">
            Add Shot Manually
          </button>
        </form>

        {shots.length === 0 ? (
          <p className="text-sm text-slate-500">No shots yet.</p>
        ) : (
          <ul className="divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white">
            {shots.map((shot) => (
              <li key={shot.id} className="flex items-center justify-between px-4 py-3">
                <div className="flex items-center gap-3">
                  <div className="flex h-12 w-20 shrink-0 items-center justify-center overflow-hidden rounded bg-slate-100">
                    {shot.active_image_generation?.output_path ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={mediaUrl(shot.active_image_generation.output_path)}
                        alt={`Shot ${shot.shot_number} storyboard`}
                        className="h-full w-full object-cover"
                      />
                    ) : (
                      <span className="text-[10px] text-slate-400">No image</span>
                    )}
                  </div>
                  <div>
                    <Link
                      href={`/series/${seriesId}/episodes/${episodeId}/scenes/${sceneId}/shots/${shot.id}`}
                      className="font-medium hover:underline"
                    >
                      Shot {shot.shot_number}: {shot.shot_type}
                    </Link>
                    <p className="text-xs text-slate-500">{shot.action || "(no action description)"}</p>
                    <div className="mt-0.5 flex flex-wrap items-center gap-1">
                      {shot.active_image_generation && (
                        <span
                          className={`inline-block rounded px-1.5 py-0.5 text-[11px] font-medium ${
                            shot.active_image_generation.approval_status === "APPROVED"
                              ? "bg-green-100 text-green-700"
                              : shot.active_image_generation.approval_status === "REJECTED"
                                ? "bg-red-100 text-red-700"
                                : "bg-slate-100 text-slate-600"
                          }`}
                        >
                          {shot.active_image_generation.approval_status}
                        </span>
                      )}
                      {shot.active_dialogue_generation && (
                        <span className="inline-block rounded bg-slate-100 px-1.5 py-0.5 text-[11px] font-medium text-slate-600">
                          Dialogue audio
                        </span>
                      )}
                      {shot.active_narration_generation && (
                        <span className="inline-block rounded bg-slate-100 px-1.5 py-0.5 text-[11px] font-medium text-slate-600">
                          Narration audio
                        </span>
                      )}
                      {shot.active_video_generation && (
                        <span className="inline-block rounded bg-slate-100 px-1.5 py-0.5 text-[11px] font-medium text-slate-600">
                          Video
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <Link
                  href={`/series/${seriesId}/episodes/${episodeId}/scenes/${sceneId}/shots/${shot.id}`}
                  className="text-sm text-slate-500 hover:underline"
                >
                  Edit →
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

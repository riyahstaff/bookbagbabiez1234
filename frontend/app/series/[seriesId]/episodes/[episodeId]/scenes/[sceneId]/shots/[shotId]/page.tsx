"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  buildShotPrompt,
  deleteShot,
  getShot,
  listCharacters,
  setShotCharacters,
  updateShot,
} from "@/lib/api";
import { TextField, TextAreaField, SelectField } from "@/components/Field";
import StoryboardPanel from "@/components/StoryboardPanel";
import VoicePanel from "@/components/VoicePanel";
import { SHOT_TYPES, type Character, type Shot, type ShotInput, type ShotType } from "@/lib/types";

export default function ShotDetailPage() {
  const params = useParams<{ seriesId: string; episodeId: string; sceneId: string; shotId: string }>();
  const seriesId = Number(params.seriesId);
  const episodeId = Number(params.episodeId);
  const sceneId = Number(params.sceneId);
  const shotId = Number(params.shotId);
  const router = useRouter();

  const [shot, setShot] = useState<Shot | null>(null);
  const [form, setForm] = useState<ShotInput>({});
  const [characters, setCharacters] = useState<Character[]>([]);
  const [selectedCharacterIds, setSelectedCharacterIds] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [buildingPrompt, setBuildingPrompt] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedAt, setSavedAt] = useState<number | null>(null);

  function refreshShot() {
    return getShot(shotId).then((data) => {
      setShot(data);
      setForm(data);
      return data;
    });
  }

  useEffect(() => {
    refreshShot()
      .then((data) => {
        setSelectedCharacterIds(new Set(data.characters.map((c) => c.character_id)));
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load shot"))
      .finally(() => setLoading(false));
    listCharacters(seriesId).then(setCharacters);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [shotId, seriesId]);

  async function handleBuildPrompt() {
    setBuildingPrompt(true);
    setError(null);
    try {
      const updated = await buildShotPrompt(shotId);
      setShot(updated);
      setForm(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to build prompt");
    } finally {
      setBuildingPrompt(false);
    }
  }

  function set<K extends keyof ShotInput>(key: K, value: ShotInput[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSave(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const updated = await updateShot(shotId, form);
      setShot(updated);
      setForm(updated);
      setSavedAt(Date.now());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save shot");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!confirm(`Delete Shot ${shot?.shot_number}?`)) return;
    try {
      await deleteShot(shotId);
      router.push(`/series/${seriesId}/episodes/${episodeId}/scenes/${sceneId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete shot");
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
      const updated = await setShotCharacters(
        shotId,
        Array.from(selectedCharacterIds).map((id) => ({ character_id: id, outfit_id: null })),
      );
      setShot(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save character list");
    }
  }

  if (loading) return <p className="text-sm text-slate-500">Loading...</p>;
  if (!shot) return <p className="text-sm text-red-700">{error ?? "Shot not found."}</p>;

  return (
    <div className="space-y-8">
      <div className="flex items-start justify-between">
        <div>
          <Link
            href={`/series/${seriesId}/episodes/${episodeId}/scenes/${sceneId}`}
            className="text-sm text-slate-500 hover:underline"
          >
            ← Back to scene
          </Link>
          <h1 className="mt-1 text-2xl font-semibold">Shot {shot.shot_number}</h1>
        </div>
        <button
          onClick={handleDelete}
          className="rounded border border-red-200 px-3 py-1.5 text-sm text-red-700 hover:bg-red-50"
        >
          Delete Shot
        </button>
      </div>

      {error && <p className="rounded bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
      {savedAt && <p className="rounded bg-green-50 px-3 py-2 text-sm text-green-700">Saved.</p>}

      <form onSubmit={handleSave} className="space-y-4 rounded-lg border border-slate-200 bg-white p-4">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <TextField
            label="Shot #"
            type="number"
            value={form.shot_number ?? shot.shot_number}
            onChange={(e) => set("shot_number", Number(e.target.value))}
          />
          <SelectField
            label="Shot Type"
            value={form.shot_type ?? shot.shot_type}
            onChange={(e) => set("shot_type", e.target.value as ShotType)}
          >
            {SHOT_TYPES.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </SelectField>
          <TextField
            label="Camera Angle"
            value={form.camera_angle ?? ""}
            onChange={(e) => set("camera_angle", e.target.value)}
            placeholder="eye level, low angle, bird's eye..."
          />
          <TextField
            label="Camera Movement"
            value={form.camera_movement ?? ""}
            onChange={(e) => set("camera_movement", e.target.value)}
            placeholder="static, slow push in, handheld..."
          />
          <TextField
            label="Emotion"
            value={form.emotion ?? ""}
            onChange={(e) => set("emotion", e.target.value)}
          />
          <TextField
            label="Lighting"
            value={form.lighting ?? ""}
            onChange={(e) => set("lighting", e.target.value)}
          />
          <TextField
            label="Duration (seconds)"
            type="number"
            value={form.duration_seconds ?? ""}
            onChange={(e) => set("duration_seconds", e.target.value ? Number(e.target.value) : null)}
          />
        </div>

        <TextAreaField
          label="Action"
          rows={2}
          value={form.action ?? ""}
          onChange={(e) => set("action", e.target.value)}
        />
        <TextAreaField
          label="Dialogue"
          rows={2}
          value={form.dialogue ?? ""}
          onChange={(e) => set("dialogue", e.target.value)}
        />
        <TextAreaField
          label="Narration"
          rows={2}
          value={form.narration ?? ""}
          onChange={(e) => set("narration", e.target.value)}
        />
        <div className="flex items-end gap-3">
          <div className="flex-1">
            <TextAreaField
              label="Visual Prompt"
              rows={3}
              value={form.visual_prompt ?? ""}
              onChange={(e) => set("visual_prompt", e.target.value)}
              placeholder="Editable before any generation is requested - construct from the Series/Character Bible plus this shot's fields."
            />
          </div>
          <button
            type="button"
            onClick={handleBuildPrompt}
            disabled={buildingPrompt}
            className="rounded border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50 disabled:opacity-50"
          >
            {buildingPrompt ? "Building..." : "Build Prompt"}
          </button>
        </div>
        <TextAreaField
          label="Negative Prompt"
          rows={2}
          value={form.negative_prompt ?? ""}
          onChange={(e) => set("negative_prompt", e.target.value)}
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
        <h2 className="text-lg font-medium">Characters Visible</h2>
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

      <StoryboardPanel shotId={shotId} onShotChanged={refreshShot} />
      <VoicePanel shotId={shotId} seriesId={seriesId} track="DIALOGUE" text={shot.dialogue} onShotChanged={refreshShot} />
      <VoicePanel shotId={shotId} seriesId={seriesId} track="NARRATION" text={shot.narration} onShotChanged={refreshShot} />
    </div>
  );
}

"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  deleteVoice,
  listCharacters,
  mediaUrl,
  updateVoice,
  uploadVoiceReferenceAudio,
} from "@/lib/api";
import { CheckboxField, SelectField, TextAreaField, TextField } from "@/components/Field";
import type { Character, Voice, VoiceInput } from "@/lib/types";
import { listVoices } from "@/lib/api";

export default function VoiceDetailPage() {
  const params = useParams<{ seriesId: string; voiceId: string }>();
  const seriesId = Number(params.seriesId);
  const voiceId = Number(params.voiceId);
  const router = useRouter();

  const [voice, setVoice] = useState<Voice | null>(null);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [form, setForm] = useState<VoiceInput>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedAt, setSavedAt] = useState<number | null>(null);

  useEffect(() => {
    Promise.all([listVoices(seriesId), listCharacters(seriesId)])
      .then(([voices, loadedCharacters]) => {
        const found = voices.find((v) => v.id === voiceId);
        if (!found) throw new Error("Voice not found");
        setVoice(found);
        setForm(found);
        setCharacters(loadedCharacters);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load voice"))
      .finally(() => setLoading(false));
  }, [seriesId, voiceId]);

  function set<K extends keyof VoiceInput>(key: K, value: VoiceInput[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSave(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const updated = await updateVoice(voiceId, form);
      setVoice(updated);
      setForm(updated);
      setSavedAt(Date.now());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save voice");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!confirm(`Delete voice "${voice?.name}"?`)) return;
    try {
      await deleteVoice(voiceId);
      router.push(`/series/${seriesId}/voices`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete voice");
    }
  }

  async function handleUploadAudio(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const updated = await uploadVoiceReferenceAudio(voiceId, file);
      setVoice(updated);
      setForm(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to upload reference audio");
    } finally {
      setUploading(false);
    }
  }

  if (loading) return <p className="text-sm text-slate-500">Loading...</p>;
  if (!voice) return <p className="text-sm text-red-700">{error ?? "Voice not found."}</p>;

  return (
    <div className="space-y-8">
      <div className="flex items-start justify-between">
        <div>
          <Link href={`/series/${seriesId}/voices`} className="text-sm text-slate-500 hover:underline">
            ← Back to voices
          </Link>
          <p className="mt-1 text-xs font-medium uppercase text-slate-400">{voice.voice_code}</p>
          <h1 className="text-2xl font-semibold">{voice.name}</h1>
        </div>
        <button
          onClick={handleDelete}
          className="rounded border border-red-200 px-3 py-1.5 text-sm text-red-700 hover:bg-red-50"
        >
          Delete Voice
        </button>
      </div>

      {error && <p className="rounded bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
      {savedAt && <p className="rounded bg-green-50 px-3 py-2 text-sm text-green-700">Saved.</p>}

      <form onSubmit={handleSave} className="space-y-4 rounded-lg border border-slate-200 bg-white p-4">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <TextField label="Name" value={form.name ?? ""} onChange={(e) => set("name", e.target.value)} />
          <SelectField
            label="Character"
            value={form.character_id ?? ""}
            onChange={(e) => set("character_id", e.target.value ? Number(e.target.value) : null)}
          >
            <option value="">Narrator / standalone</option>
            {characters.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </SelectField>
          <TextField label="Provider" value={form.provider ?? ""} onChange={(e) => set("provider", e.target.value)} placeholder="chatterbox" />
          <TextField
            label="Provider Voice ID"
            value={form.provider_voice_id ?? ""}
            onChange={(e) => set("provider_voice_id", e.target.value)}
          />
          <TextField label="Emotion" value={form.emotion ?? ""} onChange={(e) => set("emotion", e.target.value)} />
          <TextField
            label="Speed"
            type="number"
            step="0.1"
            value={form.speed ?? ""}
            onChange={(e) => set("speed", e.target.value ? Number(e.target.value) : null)}
          />
          <TextField
            label="Pitch"
            type="number"
            step="0.1"
            value={form.pitch ?? ""}
            onChange={(e) => set("pitch", e.target.value ? Number(e.target.value) : null)}
          />
        </div>

        <CheckboxField
          label="Default voice for this character/series"
          checked={form.is_default ?? false}
          onChange={(e) => set("is_default", e.target.checked)}
        />

        <TextAreaField
          label="Description"
          rows={2}
          value={form.description ?? ""}
          onChange={(e) => set("description", e.target.value)}
        />
        <TextAreaField
          label="Speaking Style"
          rows={2}
          value={form.speaking_style ?? ""}
          onChange={(e) => set("speaking_style", e.target.value)}
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
        <h2 className="text-lg font-medium">Reference Audio</h2>
        <p className="text-xs text-slate-500">
          Only upload reference audio you have the rights to clone. Real (non-mock) voice providers may
          embed an inaudible watermark in generated output - e.g. Chatterbox&apos;s PerTh watermark - and
          any AI-voiced content should be disclosed to your audience where required.
        </p>
        {voice.reference_audio_path ? (
          // eslint-disable-next-line jsx-a11y/media-has-caption
          <audio controls src={mediaUrl(voice.reference_audio_path)} className="w-full max-w-md" />
        ) : (
          <p className="text-sm text-slate-500">No reference audio uploaded yet.</p>
        )}
        <div>
          <label className="text-xs font-medium text-slate-600">
            {voice.reference_audio_path ? "Replace audio file" : "Upload audio file"}
          </label>
          <input type="file" accept="audio/*" onChange={handleUploadAudio} disabled={uploading} className="block text-sm" />
        </div>
      </section>
    </div>
  );
}

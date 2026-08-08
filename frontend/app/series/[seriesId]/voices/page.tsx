"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { createVoice, listCharacters, listVoices } from "@/lib/api";
import { TextField, SelectField } from "@/components/Field";
import type { Character, Voice } from "@/lib/types";

export default function VoiceListPage() {
  const params = useParams<{ seriesId: string }>();
  const seriesId = Number(params.seriesId);

  const [voices, setVoices] = useState<Voice[]>([]);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [characterId, setCharacterId] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);

  async function refresh() {
    setLoading(true);
    try {
      const [loadedVoices, loadedCharacters] = await Promise.all([
        listVoices(seriesId),
        listCharacters(seriesId),
      ]);
      setVoices(loadedVoices);
      setCharacters(loadedCharacters);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load voices");
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
    if (!name.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      await createVoice(seriesId, {
        name,
        character_id: characterId ? Number(characterId) : null,
      });
      setName("");
      setCharacterId("");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create voice");
    } finally {
      setSubmitting(false);
    }
  }

  function characterName(id: number | null) {
    if (id === null) return "Narrator / standalone";
    return characters.find((c) => c.id === id)?.name ?? `#${id}`;
  }

  return (
    <div className="space-y-8">
      <div>
        <Link href={`/series/${seriesId}`} className="text-sm text-slate-500 hover:underline">
          ← Back to series
        </Link>
        <h1 className="mt-1 text-2xl font-semibold">Voices</h1>
        <p className="text-sm text-slate-500">
          Persistent voices for characters, plus the series narrator. Generate dialogue and narration
          audio for a specific line from a shot&apos;s detail page.
        </p>
      </div>

      {error && <p className="rounded bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

      <form onSubmit={handleCreate} className="flex flex-wrap items-end gap-3 rounded-lg border border-slate-200 bg-white p-4">
        <TextField label="Name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Marcus Main" required />
        <SelectField label="Character" value={characterId} onChange={(e) => setCharacterId(e.target.value)}>
          <option value="">Narrator / standalone</option>
          {characters.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </SelectField>
        <button
          type="submit"
          disabled={submitting}
          className="rounded bg-slate-900 px-4 py-1.5 text-sm font-medium text-white disabled:opacity-50"
        >
          {submitting ? "Creating..." : "Create Voice"}
        </button>
      </form>

      {loading ? (
        <p className="text-sm text-slate-500">Loading...</p>
      ) : voices.length === 0 ? (
        <p className="text-sm text-slate-500">No voices yet. Create one above.</p>
      ) : (
        <ul className="divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white">
          {voices.map((voice) => (
            <li key={voice.id} className="flex items-center justify-between px-4 py-3">
              <div>
                <Link href={`/series/${seriesId}/voices/${voice.id}`} className="font-medium hover:underline">
                  {voice.name}
                </Link>
                <p className="text-xs text-slate-500">
                  {voice.voice_code} · {characterName(voice.character_id)}
                  {voice.is_default ? " · default" : ""}
                </p>
              </div>
              <Link href={`/series/${seriesId}/voices/${voice.id}`} className="text-sm text-slate-500 hover:underline">
                Edit →
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

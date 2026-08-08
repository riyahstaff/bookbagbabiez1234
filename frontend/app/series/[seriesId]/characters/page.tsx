"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { createCharacter, listCharacters } from "@/lib/api";
import { TextField } from "@/components/Field";
import type { Character } from "@/lib/types";

export default function CharacterListPage() {
  const params = useParams<{ seriesId: string }>();
  const seriesId = Number(params.seriesId);

  const [characters, setCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function refresh() {
    setLoading(true);
    try {
      setCharacters(await listCharacters(seriesId));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load characters");
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
      await createCharacter(seriesId, { name, description: description || null });
      setName("");
      setDescription("");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create character");
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
        <h1 className="mt-1 text-2xl font-semibold">Characters</h1>
        <p className="text-sm text-slate-500">
          Every recurring character gets a persistent ID (e.g. CHAR_MARCUS_001) so references and
          voices stay attached to it across the whole series.
        </p>
      </div>

      {error && <p className="rounded bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

      <form
        onSubmit={handleCreate}
        className="flex flex-wrap items-end gap-3 rounded-lg border border-slate-200 bg-white p-4"
      >
        <TextField label="Name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Marcus" required />
        <TextField
          label="Short Description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="The hero of the show"
          className="w-64"
        />
        <button
          type="submit"
          disabled={submitting}
          className="rounded bg-slate-900 px-4 py-1.5 text-sm font-medium text-white disabled:opacity-50"
        >
          {submitting ? "Creating..." : "Create Character"}
        </button>
      </form>

      {loading ? (
        <p className="text-sm text-slate-500">Loading...</p>
      ) : characters.length === 0 ? (
        <p className="text-sm text-slate-500">No characters yet. Create your first one above.</p>
      ) : (
        <ul className="divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white">
          {characters.map((character) => (
            <li key={character.id} className="flex items-center justify-between px-4 py-3">
              <div>
                <Link
                  href={`/series/${seriesId}/characters/${character.id}`}
                  className="font-medium hover:underline"
                >
                  {character.name}
                </Link>
                <p className="text-xs text-slate-500">
                  {character.character_code}
                  {character.description ? ` · ${character.description}` : ""}
                </p>
              </div>
              <Link
                href={`/series/${seriesId}/characters/${character.id}`}
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

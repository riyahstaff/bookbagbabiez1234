"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { createCharacter, listCharacterReferences, listCharacters, mediaUrl } from "@/lib/api";
import { TextField } from "@/components/Field";
import type { Character } from "@/lib/types";

export default function CharacterListPage() {
  const params = useParams<{ seriesId: string }>();
  const seriesId = Number(params.seriesId);

  const [characters, setCharacters] = useState<Character[]>([]);
  const [thumbnails, setThumbnails] = useState<Record<number, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function refresh() {
    setLoading(true);
    try {
      const loaded = await listCharacters(seriesId);
      setCharacters(loaded);
      setError(null);

      const entries = await Promise.all(
        loaded.map(async (character) => {
          const refs = await listCharacterReferences(character.id).catch(() => []);
          const front = refs.find((r) => r.category === "FRONT") ?? refs[0];
          return [character.id, front ? mediaUrl(front.image_path) : null] as const;
        }),
      );
      setThumbnails(
        Object.fromEntries(entries.filter(([, url]) => url !== null)) as Record<number, string>,
      );
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
              <div className="flex items-center gap-3">
                <Link
                  href={`/series/${seriesId}/characters/${character.id}`}
                  className="flex h-12 w-12 shrink-0 items-center justify-center overflow-hidden rounded-full bg-slate-100"
                >
                  {thumbnails[character.id] ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={thumbnails[character.id]}
                      alt={character.name}
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    <span className="text-xs text-slate-400">No photo</span>
                  )}
                </Link>
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

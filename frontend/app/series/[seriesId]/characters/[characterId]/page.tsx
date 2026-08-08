"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  createOutfit,
  deleteCharacter,
  deleteCharacterReference,
  deleteOutfit,
  getCharacter,
  listCharacterReferences,
  listOutfits,
  mediaUrl,
  updateCharacter,
  uploadCharacterReference,
} from "@/lib/api";
import { TextField, TextAreaField } from "@/components/Field";
import ReferenceGallery from "@/components/ReferenceGallery";
import OutfitCard from "@/components/OutfitCard";
import {
  CHARACTER_REFERENCE_CATEGORIES,
  type Character,
  type CharacterInput,
  type CharacterOutfit,
  type CharacterReference,
} from "@/lib/types";

export default function CharacterDetailPage() {
  const params = useParams<{ seriesId: string; characterId: string }>();
  const seriesId = Number(params.seriesId);
  const characterId = Number(params.characterId);
  const router = useRouter();

  const [character, setCharacter] = useState<Character | null>(null);
  const [form, setForm] = useState<CharacterInput>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedAt, setSavedAt] = useState<number | null>(null);

  const [references, setReferences] = useState<CharacterReference[]>([]);
  const [outfits, setOutfits] = useState<CharacterOutfit[]>([]);
  const [newOutfitName, setNewOutfitName] = useState("");

  useEffect(() => {
    getCharacter(characterId)
      .then((data) => {
        setCharacter(data);
        setForm(data);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load character"))
      .finally(() => setLoading(false));
    listCharacterReferences(characterId).then(setReferences);
    listOutfits(characterId).then(setOutfits);
  }, [characterId]);

  function set<K extends keyof CharacterInput>(key: K, value: CharacterInput[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSave(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const updated = await updateCharacter(characterId, form);
      setCharacter(updated);
      setForm(updated);
      setSavedAt(Date.now());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save character");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!confirm(`Delete "${character?.name}"?`)) return;
    try {
      await deleteCharacter(characterId);
      router.push(`/series/${seriesId}/characters`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete character");
    }
  }

  async function handleCreateOutfit(event: React.FormEvent) {
    event.preventDefault();
    if (!newOutfitName.trim()) return;
    const outfit = await createOutfit(characterId, newOutfitName);
    setOutfits((prev) => [...prev, outfit]);
    setNewOutfitName("");
  }

  async function handleDeleteOutfit(outfitId: number) {
    await deleteOutfit(outfitId);
    setOutfits((prev) => prev.filter((o) => o.id !== outfitId));
  }

  if (loading) return <p className="text-sm text-slate-500">Loading...</p>;
  if (!character) return <p className="text-sm text-red-700">{error ?? "Character not found."}</p>;

  return (
    <div className="space-y-8">
      <div className="flex items-start justify-between">
        <div>
          <Link href={`/series/${seriesId}/characters`} className="text-sm text-slate-500 hover:underline">
            ← Back to characters
          </Link>
          <p className="mt-1 text-xs font-medium uppercase text-slate-400">{character.character_code}</p>
          <h1 className="text-2xl font-semibold">{character.name}</h1>
        </div>
        <button
          onClick={handleDelete}
          className="rounded border border-red-200 px-3 py-1.5 text-sm text-red-700 hover:bg-red-50"
        >
          Delete Character
        </button>
      </div>

      {error && <p className="rounded bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
      {savedAt && <p className="rounded bg-green-50 px-3 py-2 text-sm text-green-700">Saved.</p>}

      <section className="space-y-3 rounded-lg border border-slate-200 bg-white p-4">
        <div>
          <h2 className="text-lg font-medium">Reference Images</h2>
          <p className="text-sm text-slate-500">
            Upload a picture of this character here. It gets pulled into every generation request
            involving them, so their look stays consistent shot to shot instead of drifting.
          </p>
        </div>
        <ReferenceGallery
          tagLabel="Category"
          categories={CHARACTER_REFERENCE_CATEGORIES}
          items={references.map((r) => ({ id: r.id, imageUrl: mediaUrl(r.image_path), tag: r.category }))}
          onUpload={async (file, category) => {
            await uploadCharacterReference(
              characterId,
              file,
              category as (typeof CHARACTER_REFERENCE_CATEGORIES)[number],
            );
            setReferences(await listCharacterReferences(characterId));
          }}
          onDelete={async (id) => {
            await deleteCharacterReference(id);
            setReferences(await listCharacterReferences(characterId));
          }}
        />
      </section>

      <form onSubmit={handleSave} className="space-y-4 rounded-lg border border-slate-200 bg-white p-4">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <TextField label="Name" value={form.name ?? ""} onChange={(e) => set("name", e.target.value)} />
          <TextField label="Age Range" value={form.age_range ?? ""} onChange={(e) => set("age_range", e.target.value)} />
          <TextField label="Height" value={form.height ?? ""} onChange={(e) => set("height", e.target.value)} />
          <TextField label="Build" value={form.build ?? ""} onChange={(e) => set("build", e.target.value)} />
          <TextField label="Skin Tone" value={form.skin_tone ?? ""} onChange={(e) => set("skin_tone", e.target.value)} />
          <TextField label="Hair" value={form.hair ?? ""} onChange={(e) => set("hair", e.target.value)} />
          <TextField label="Accent" value={form.accent ?? ""} onChange={(e) => set("accent", e.target.value)} />
        </div>

        <TextAreaField
          label="Description"
          rows={2}
          value={form.description ?? ""}
          onChange={(e) => set("description", e.target.value)}
        />
        <TextAreaField
          label="Facial Features"
          rows={2}
          value={form.facial_features ?? ""}
          onChange={(e) => set("facial_features", e.target.value)}
        />
        <TextAreaField
          label="Clothing"
          rows={2}
          value={form.clothing ?? ""}
          onChange={(e) => set("clothing", e.target.value)}
        />
        <TextAreaField
          label="Accessories"
          rows={2}
          value={form.accessories ?? ""}
          onChange={(e) => set("accessories", e.target.value)}
        />
        <TextAreaField
          label="Personality"
          rows={2}
          value={form.personality ?? ""}
          onChange={(e) => set("personality", e.target.value)}
        />
        <TextAreaField
          label="Movement Style"
          rows={2}
          value={form.movement_style ?? ""}
          onChange={(e) => set("movement_style", e.target.value)}
        />
        <TextAreaField
          label="Speaking Style"
          rows={2}
          value={form.speaking_style ?? ""}
          onChange={(e) => set("speaking_style", e.target.value)}
        />
        <TextAreaField
          label="Visual Style Notes"
          rows={2}
          value={form.visual_style_notes ?? ""}
          onChange={(e) => set("visual_style_notes", e.target.value)}
        />
        <TextAreaField
          label="Continuity Restrictions"
          rows={2}
          value={form.continuity_restrictions ?? ""}
          onChange={(e) => set("continuity_restrictions", e.target.value)}
          placeholder="Never changes hairstyle. Always wears the blue jacket unless scripted otherwise."
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
        <div>
          <h2 className="text-lg font-medium">Outfits</h2>
          <p className="text-sm text-slate-500">
            Identity stays separate from wardrobe - each scene references a specific outfit instead of
            re-describing clothing every time, which is what prevents wardrobe drift.
          </p>
        </div>
        <form onSubmit={handleCreateOutfit} className="flex items-end gap-3 rounded-lg border border-slate-200 bg-white p-3">
          <TextField
            label="New Outfit Name"
            value={newOutfitName}
            onChange={(e) => setNewOutfitName(e.target.value)}
            placeholder="Casual"
          />
          <button
            type="submit"
            className="rounded bg-slate-900 px-4 py-1.5 text-sm font-medium text-white"
          >
            Add Outfit
          </button>
        </form>
        {outfits.length === 0 ? (
          <p className="text-sm text-slate-500">No outfits yet.</p>
        ) : (
          <div className="space-y-2">
            {outfits.map((outfit) => (
              <OutfitCard key={outfit.id} outfit={outfit} onDelete={handleDeleteOutfit} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

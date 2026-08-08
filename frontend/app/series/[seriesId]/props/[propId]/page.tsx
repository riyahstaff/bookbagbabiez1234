"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  deleteProp,
  deletePropReference,
  getProp,
  listPropReferences,
  mediaUrl,
  updateProp,
  uploadPropReference,
} from "@/lib/api";
import { TextField, TextAreaField } from "@/components/Field";
import ReferenceGallery from "@/components/ReferenceGallery";
import type { Prop, PropInput, PropReference } from "@/lib/types";

export default function PropDetailPage() {
  const params = useParams<{ seriesId: string; propId: string }>();
  const seriesId = Number(params.seriesId);
  const propId = Number(params.propId);
  const router = useRouter();

  const [prop, setProp] = useState<Prop | null>(null);
  const [form, setForm] = useState<PropInput>({});
  const [references, setReferences] = useState<PropReference[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedAt, setSavedAt] = useState<number | null>(null);

  useEffect(() => {
    getProp(propId)
      .then((data) => {
        setProp(data);
        setForm(data);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load prop"))
      .finally(() => setLoading(false));
    listPropReferences(propId).then(setReferences);
  }, [propId]);

  function set<K extends keyof PropInput>(key: K, value: PropInput[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSave(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const updated = await updateProp(propId, form);
      setProp(updated);
      setForm(updated);
      setSavedAt(Date.now());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save prop");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!confirm(`Delete "${prop?.name}"?`)) return;
    try {
      await deleteProp(propId);
      router.push(`/series/${seriesId}/props`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete prop");
    }
  }

  if (loading) return <p className="text-sm text-slate-500">Loading...</p>;
  if (!prop) return <p className="text-sm text-red-700">{error ?? "Prop not found."}</p>;

  return (
    <div className="space-y-8">
      <div className="flex items-start justify-between">
        <div>
          <Link href={`/series/${seriesId}/props`} className="text-sm text-slate-500 hover:underline">
            ← Back to props
          </Link>
          <p className="mt-1 text-xs font-medium uppercase text-slate-400">{prop.prop_code}</p>
          <h1 className="text-2xl font-semibold">{prop.name}</h1>
        </div>
        <button
          onClick={handleDelete}
          className="rounded border border-red-200 px-3 py-1.5 text-sm text-red-700 hover:bg-red-50"
        >
          Delete Prop
        </button>
      </div>

      {error && <p className="rounded bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
      {savedAt && <p className="rounded bg-green-50 px-3 py-2 text-sm text-green-700">Saved.</p>}

      <form onSubmit={handleSave} className="space-y-4 rounded-lg border border-slate-200 bg-white p-4">
        <TextField label="Name" value={form.name ?? ""} onChange={(e) => set("name", e.target.value)} />
        <TextAreaField
          label="Description"
          rows={2}
          value={form.description ?? ""}
          onChange={(e) => set("description", e.target.value)}
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
        <h2 className="text-lg font-medium">Reference Images</h2>
        <ReferenceGallery
          tagLabel="Label"
          items={references.map((r) => ({ id: r.id, imageUrl: mediaUrl(r.image_path), tag: r.label }))}
          onUpload={async (file, label) => {
            await uploadPropReference(propId, file, label || undefined);
            setReferences(await listPropReferences(propId));
          }}
          onDelete={async (id) => {
            await deletePropReference(id);
            setReferences(await listPropReferences(propId));
          }}
        />
      </section>
    </div>
  );
}

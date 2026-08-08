"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  deleteLocation,
  deleteLocationReference,
  getLocation,
  listLocationReferences,
  mediaUrl,
  updateLocation,
  uploadLocationReference,
} from "@/lib/api";
import { TextField, TextAreaField } from "@/components/Field";
import ReferenceGallery from "@/components/ReferenceGallery";
import {
  LOCATION_REFERENCE_CATEGORIES,
  type Location,
  type LocationInput,
  type LocationReference,
} from "@/lib/types";

export default function LocationDetailPage() {
  const params = useParams<{ seriesId: string; locationId: string }>();
  const seriesId = Number(params.seriesId);
  const locationId = Number(params.locationId);
  const router = useRouter();

  const [location, setLocation] = useState<Location | null>(null);
  const [form, setForm] = useState<LocationInput>({});
  const [references, setReferences] = useState<LocationReference[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedAt, setSavedAt] = useState<number | null>(null);

  useEffect(() => {
    getLocation(locationId)
      .then((data) => {
        setLocation(data);
        setForm(data);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load location"))
      .finally(() => setLoading(false));
    listLocationReferences(locationId).then(setReferences);
  }, [locationId]);

  function set<K extends keyof LocationInput>(key: K, value: LocationInput[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSave(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const updated = await updateLocation(locationId, form);
      setLocation(updated);
      setForm(updated);
      setSavedAt(Date.now());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save location");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!confirm(`Delete "${location?.name}"?`)) return;
    try {
      await deleteLocation(locationId);
      router.push(`/series/${seriesId}/locations`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete location");
    }
  }

  if (loading) return <p className="text-sm text-slate-500">Loading...</p>;
  if (!location) return <p className="text-sm text-red-700">{error ?? "Location not found."}</p>;

  return (
    <div className="space-y-8">
      <div className="flex items-start justify-between">
        <div>
          <Link href={`/series/${seriesId}/locations`} className="text-sm text-slate-500 hover:underline">
            ← Back to locations
          </Link>
          <p className="mt-1 text-xs font-medium uppercase text-slate-400">{location.location_code}</p>
          <h1 className="text-2xl font-semibold">{location.name}</h1>
        </div>
        <button
          onClick={handleDelete}
          className="rounded border border-red-200 px-3 py-1.5 text-sm text-red-700 hover:bg-red-50"
        >
          Delete Location
        </button>
      </div>

      {error && <p className="rounded bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
      {savedAt && <p className="rounded bg-green-50 px-3 py-2 text-sm text-green-700">Saved.</p>}

      <form onSubmit={handleSave} className="space-y-4 rounded-lg border border-slate-200 bg-white p-4">
        <TextField label="Name" value={form.name ?? ""} onChange={(e) => set("name", e.target.value)} />
        <TextAreaField label="Description" rows={2} value={form.description ?? ""} onChange={(e) => set("description", e.target.value)} />
        <TextAreaField label="Lighting" rows={2} value={form.lighting_notes ?? ""} onChange={(e) => set("lighting_notes", e.target.value)} />
        <TextAreaField
          label="Time-of-Day Versions"
          rows={2}
          value={form.time_of_day_notes ?? ""}
          onChange={(e) => set("time_of_day_notes", e.target.value)}
        />
        <TextAreaField
          label="Camera Reference Angles"
          rows={2}
          value={form.camera_reference_notes ?? ""}
          onChange={(e) => set("camera_reference_notes", e.target.value)}
        />
        <TextAreaField
          label="Important Props"
          rows={2}
          value={form.important_props ?? ""}
          onChange={(e) => set("important_props", e.target.value)}
        />
        <TextAreaField
          label="Visual Continuity Rules"
          rows={2}
          value={form.continuity_rules ?? ""}
          onChange={(e) => set("continuity_rules", e.target.value)}
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
          tagLabel="Category"
          categories={LOCATION_REFERENCE_CATEGORIES}
          items={references.map((r) => ({ id: r.id, imageUrl: mediaUrl(r.image_path), tag: r.category }))}
          onUpload={async (file, category) => {
            await uploadLocationReference(
              locationId,
              file,
              category as (typeof LOCATION_REFERENCE_CATEGORIES)[number],
            );
            setReferences(await listLocationReferences(locationId));
          }}
          onDelete={async (id) => {
            await deleteLocationReference(id);
            setReferences(await listLocationReferences(locationId));
          }}
        />
      </section>
    </div>
  );
}

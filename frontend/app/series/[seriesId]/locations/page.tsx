"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { createLocation, listLocations } from "@/lib/api";
import { TextField } from "@/components/Field";
import type { Location } from "@/lib/types";

export default function LocationListPage() {
  const params = useParams<{ seriesId: string }>();
  const seriesId = Number(params.seriesId);

  const [locations, setLocations] = useState<Location[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function refresh() {
    setLoading(true);
    try {
      setLocations(await listLocations(seriesId));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load locations");
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
      await createLocation(seriesId, { name });
      setName("");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create location");
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
        <h1 className="mt-1 text-2xl font-semibold">Locations</h1>
        <p className="text-sm text-slate-500">
          Reusable sets. The pipeline should reach for one of these before generating a new background.
        </p>
      </div>

      {error && <p className="rounded bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

      <form onSubmit={handleCreate} className="flex flex-wrap items-end gap-3 rounded-lg border border-slate-200 bg-white p-4">
        <TextField label="Name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Diner" required />
        <button
          type="submit"
          disabled={submitting}
          className="rounded bg-slate-900 px-4 py-1.5 text-sm font-medium text-white disabled:opacity-50"
        >
          {submitting ? "Creating..." : "Create Location"}
        </button>
      </form>

      {loading ? (
        <p className="text-sm text-slate-500">Loading...</p>
      ) : locations.length === 0 ? (
        <p className="text-sm text-slate-500">No locations yet. Create one above.</p>
      ) : (
        <ul className="divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white">
          {locations.map((location) => (
            <li key={location.id} className="flex items-center justify-between px-4 py-3">
              <div>
                <Link href={`/series/${seriesId}/locations/${location.id}`} className="font-medium hover:underline">
                  {location.name}
                </Link>
                <p className="text-xs text-slate-500">{location.location_code}</p>
              </div>
              <Link href={`/series/${seriesId}/locations/${location.id}`} className="text-sm text-slate-500 hover:underline">
                Edit →
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

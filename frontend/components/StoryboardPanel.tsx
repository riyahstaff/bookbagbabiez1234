"use client";

import { useEffect, useState } from "react";
import {
  activateGeneration,
  approveGeneration,
  deleteGeneration,
  generateStoryboard,
  listGenerations,
  mediaUrl,
  rejectGeneration,
} from "@/lib/api";
import type { Generation } from "@/lib/types";

const STATUS_COLORS: Record<Generation["status"], string> = {
  QUEUED: "bg-slate-100 text-slate-600",
  PREPARING: "bg-slate-100 text-slate-600",
  RUNNING: "bg-blue-100 text-blue-700",
  PROCESSING: "bg-blue-100 text-blue-700",
  COMPLETE: "bg-slate-100 text-slate-600",
  FAILED: "bg-red-100 text-red-700",
  CANCELED: "bg-slate-100 text-slate-600",
};

const APPROVAL_COLORS: Record<Generation["approval_status"], string> = {
  PENDING: "bg-slate-100 text-slate-600",
  APPROVED: "bg-green-100 text-green-700",
  REJECTED: "bg-red-100 text-red-700",
};

interface StoryboardPanelProps {
  shotId: number;
  onShotChanged?: () => void;
}

export default function StoryboardPanel({ shotId, onShotChanged }: StoryboardPanelProps) {
  const [generations, setGenerations] = useState<Generation[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [seed, setSeed] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);

  function refresh() {
    return listGenerations(shotId)
      .then(setGenerations)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load generations"));
  }

  useEffect(() => {
    refresh().finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [shotId]);

  async function handleGenerate() {
    setGenerating(true);
    setError(null);
    try {
      const parsedSeed = seed.trim() ? Number(seed) : null;
      await generateStoryboard(shotId, parsedSeed);
      await refresh();
      onShotChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate storyboard");
    } finally {
      setGenerating(false);
    }
  }

  async function runAction(generationId: number, action: (id: number) => Promise<Generation>) {
    setBusyId(generationId);
    setError(null);
    try {
      await action(generationId);
      await refresh();
      onShotChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed");
    } finally {
      setBusyId(null);
    }
  }

  async function handleDelete(generationId: number) {
    if (!confirm("Delete this storyboard version? This cannot be undone.")) return;
    setBusyId(generationId);
    setError(null);
    try {
      await deleteGeneration(generationId);
      await refresh();
      onShotChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete generation");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <section className="space-y-3 rounded-lg border border-slate-200 bg-white p-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-medium">Storyboard</h2>
          <p className="text-sm text-slate-500">
            Generate still frames for this shot from its visual prompt. Each attempt is kept as its own
            version - approve or activate the one to use, or delete versions you don&apos;t want.
          </p>
        </div>
      </div>

      {error && <p className="rounded bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

      <div className="flex flex-wrap items-end gap-3 rounded-lg border border-slate-200 bg-slate-50 p-3">
        <div className="flex flex-col gap-1">
          <label htmlFor="storyboard-seed" className="text-xs font-medium text-slate-600">
            Seed (optional)
          </label>
          <input
            id="storyboard-seed"
            type="number"
            value={seed}
            onChange={(e) => setSeed(e.target.value)}
            placeholder="random"
            className="w-32 rounded border border-slate-300 px-3 py-1.5 text-sm"
          />
        </div>
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="rounded bg-slate-900 px-4 py-1.5 text-sm font-medium text-white disabled:opacity-50"
        >
          {generating ? "Generating..." : "Generate Storyboard"}
        </button>
      </div>

      {loading ? (
        <p className="text-sm text-slate-500">Loading versions...</p>
      ) : generations.length === 0 ? (
        <p className="text-sm text-slate-500">No storyboard versions yet.</p>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {generations.map((generation) => (
            <div
              key={generation.id}
              className={`overflow-hidden rounded-lg border bg-white ${
                generation.is_active ? "border-slate-900 ring-1 ring-slate-900" : "border-slate-200"
              }`}
            >
              <div className="flex aspect-video items-center justify-center bg-slate-100">
                {generation.output_path ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={mediaUrl(generation.output_path)}
                    alt={`Storyboard v${generation.id}`}
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <span className="px-2 text-center text-xs text-slate-500">
                    {generation.status === "FAILED"
                      ? generation.error_message ?? "Generation failed"
                      : generation.status}
                  </span>
                )}
              </div>
              <div className="space-y-2 p-3">
                <div className="flex flex-wrap items-center gap-1.5 text-[11px]">
                  <span className={`rounded px-1.5 py-0.5 font-medium ${STATUS_COLORS[generation.status]}`}>
                    {generation.status}
                  </span>
                  <span
                    className={`rounded px-1.5 py-0.5 font-medium ${APPROVAL_COLORS[generation.approval_status]}`}
                  >
                    {generation.approval_status}
                  </span>
                  {generation.is_active && (
                    <span className="rounded bg-slate-900 px-1.5 py-0.5 font-medium text-white">Active</span>
                  )}
                  {generation.seed !== null && (
                    <span className="text-slate-500">seed={generation.seed}</span>
                  )}
                </div>
                <div className="flex flex-wrap gap-1.5">
                  <button
                    onClick={() => runAction(generation.id, approveGeneration)}
                    disabled={busyId === generation.id || generation.approval_status === "APPROVED"}
                    className="rounded border border-green-200 px-2 py-1 text-xs text-green-700 hover:bg-green-50 disabled:opacity-50"
                  >
                    Approve
                  </button>
                  <button
                    onClick={() => runAction(generation.id, rejectGeneration)}
                    disabled={busyId === generation.id || generation.approval_status === "REJECTED"}
                    className="rounded border border-red-200 px-2 py-1 text-xs text-red-700 hover:bg-red-50 disabled:opacity-50"
                  >
                    Reject
                  </button>
                  <button
                    onClick={() => runAction(generation.id, activateGeneration)}
                    disabled={busyId === generation.id || generation.is_active}
                    className="rounded border border-slate-300 px-2 py-1 text-xs hover:bg-slate-50 disabled:opacity-50"
                  >
                    Activate
                  </button>
                  <button
                    onClick={() => handleDelete(generation.id)}
                    disabled={busyId === generation.id}
                    className="rounded border border-slate-300 px-2 py-1 text-xs text-slate-500 hover:bg-slate-50 disabled:opacity-50"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

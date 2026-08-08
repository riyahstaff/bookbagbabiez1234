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
import GenerationGallery from "@/components/GenerationGallery";
import type { Generation } from "@/lib/types";

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
      .then((all) => setGenerations(all.filter((g) => g.generation_type === "IMAGE")))
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
      <div>
        <h2 className="text-lg font-medium">Storyboard</h2>
        <p className="text-sm text-slate-500">
          Generate still frames for this shot from its visual prompt. Each attempt is kept as its own
          version - approve or activate the one to use, or delete versions you don&apos;t want.
        </p>
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
      ) : (
        <GenerationGallery
          generations={generations}
          busyId={busyId}
          emptyMessage="No storyboard versions yet."
          onApprove={(id) => runAction(id, approveGeneration)}
          onReject={(id) => runAction(id, rejectGeneration)}
          onActivate={(id) => runAction(id, activateGeneration)}
          onDelete={handleDelete}
          renderPreview={(generation) => (
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
          )}
        />
      )}
    </section>
  );
}

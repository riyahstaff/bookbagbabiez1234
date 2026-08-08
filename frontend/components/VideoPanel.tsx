"use client";

import { useEffect, useState } from "react";
import {
  activateGeneration,
  approveGeneration,
  deleteGeneration,
  generateVideo,
  listGenerations,
  mediaUrl,
  rejectGeneration,
} from "@/lib/api";
import GenerationGallery from "@/components/GenerationGallery";
import type { Generation } from "@/lib/types";

function isAnimatedImage(path: string): boolean {
  return path.toLowerCase().endsWith(".gif");
}

interface VideoPanelProps {
  shotId: number;
  activeImageGeneration: Generation | null;
  onShotChanged?: () => void;
}

export default function VideoPanel({ shotId, activeImageGeneration, onShotChanged }: VideoPanelProps) {
  const [generations, setGenerations] = useState<Generation[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [seed, setSeed] = useState("");
  const [overrideGate, setOverrideGate] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);

  function refresh() {
    return listGenerations(shotId)
      .then((all) => setGenerations(all.filter((g) => g.generation_type === "VIDEO")))
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load generations"));
  }

  useEffect(() => {
    refresh().finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [shotId]);

  const hasImage = !!activeImageGeneration;
  const imageApproved = activeImageGeneration?.approval_status === "APPROVED";
  const canGenerate = hasImage && (imageApproved || overrideGate);

  async function handleGenerate() {
    if (!canGenerate) return;
    setGenerating(true);
    setError(null);
    try {
      const parsedSeed = seed.trim() ? Number(seed) : null;
      await generateVideo(shotId, { seed: parsedSeed, overrideApprovalGate: overrideGate });
      await refresh();
      onShotChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate video");
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
    if (!confirm("Delete this video version? This cannot be undone.")) return;
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
        <h2 className="text-lg font-medium">Video</h2>
        <p className="text-sm text-slate-500">
          Animates the shot&apos;s active storyboard image. Cheap image generation gates expensive video
          generation by design - an approved storyboard is required unless explicitly overridden.
        </p>
      </div>

      {error && <p className="rounded bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

      {!hasImage ? (
        <p className="rounded bg-amber-50 px-3 py-2 text-sm text-amber-700">
          This shot has no active storyboard image yet - generate and activate one above first.
        </p>
      ) : (
        <div className="flex flex-wrap items-end gap-3 rounded-lg border border-slate-200 bg-slate-50 p-3">
          <div className="flex flex-col gap-1">
            <label htmlFor="video-seed" className="text-xs font-medium text-slate-600">
              Seed (optional)
            </label>
            <input
              id="video-seed"
              type="number"
              value={seed}
              onChange={(e) => setSeed(e.target.value)}
              placeholder="random"
              className="w-32 rounded border border-slate-300 px-3 py-1.5 text-sm"
            />
          </div>
          {!imageApproved && (
            <label className="flex items-center gap-2 pb-1.5 text-sm text-amber-700">
              <input
                type="checkbox"
                checked={overrideGate}
                onChange={(e) => setOverrideGate(e.target.checked)}
                className="h-4 w-4"
              />
              The active image isn&apos;t approved yet - generate anyway
            </label>
          )}
          <button
            onClick={handleGenerate}
            disabled={generating || !canGenerate}
            className="rounded bg-slate-900 px-4 py-1.5 text-sm font-medium text-white disabled:opacity-50"
          >
            {generating ? "Generating..." : "Generate Video"}
          </button>
        </div>
      )}

      {loading ? (
        <p className="text-sm text-slate-500">Loading versions...</p>
      ) : (
        <GenerationGallery
          generations={generations}
          busyId={busyId}
          emptyMessage="No video versions yet."
          onApprove={(id) => runAction(id, approveGeneration)}
          onReject={(id) => runAction(id, rejectGeneration)}
          onActivate={(id) => runAction(id, activateGeneration)}
          onDelete={handleDelete}
          renderPreview={(generation) => (
            <div className="flex aspect-video items-center justify-center bg-slate-100">
              {generation.output_path ? (
                isAnimatedImage(generation.output_path) ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={mediaUrl(generation.output_path)}
                    alt={`Video v${generation.id}`}
                    className="h-full w-full object-cover"
                  />
                ) : (
                  // eslint-disable-next-line jsx-a11y/media-has-caption
                  <video
                    controls
                    src={mediaUrl(generation.output_path)}
                    className="h-full w-full object-cover"
                  />
                )
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

"use client";

import { useEffect, useState } from "react";
import {
  activateGeneration,
  approveGeneration,
  deleteGeneration,
  generateVoice,
  listGenerations,
  listVoices,
  mediaUrl,
  rejectGeneration,
} from "@/lib/api";
import GenerationGallery from "@/components/GenerationGallery";
import type { AudioTrack, Generation, Voice } from "@/lib/types";

interface VoicePanelProps {
  shotId: number;
  seriesId: number;
  track: AudioTrack;
  text: string | null;
  onShotChanged?: () => void;
}

export default function VoicePanel({ shotId, seriesId, track, text, onShotChanged }: VoicePanelProps) {
  const [generations, setGenerations] = useState<Generation[]>([]);
  const [voices, setVoices] = useState<Voice[]>([]);
  const [selectedVoiceId, setSelectedVoiceId] = useState("");
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [seed, setSeed] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);

  function refresh() {
    return listGenerations(shotId)
      .then((all) => setGenerations(all.filter((g) => g.audio_track === track)))
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load generations"));
  }

  useEffect(() => {
    refresh().finally(() => setLoading(false));
    listVoices(seriesId).then((loaded) => {
      setVoices(loaded);
      const preferred = loaded.find((v) => v.is_default) ?? loaded[0];
      if (preferred) setSelectedVoiceId(String(preferred.id));
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [shotId, seriesId, track]);

  async function handleGenerate() {
    if (!selectedVoiceId) return;
    setGenerating(true);
    setError(null);
    try {
      const parsedSeed = seed.trim() ? Number(seed) : null;
      await generateVoice(shotId, track, Number(selectedVoiceId), { seed: parsedSeed });
      await refresh();
      onShotChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate audio");
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
    if (!confirm("Delete this audio version? This cannot be undone.")) return;
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

  const label = track === "DIALOGUE" ? "Dialogue" : "Narration";

  return (
    <section className="space-y-3 rounded-lg border border-slate-200 bg-white p-4">
      <div>
        <h2 className="text-lg font-medium">{label} Audio</h2>
        <p className="text-sm text-slate-500">
          {text ? `"${text}"` : `This shot has no ${label.toLowerCase()} text yet - add it above first.`}
        </p>
      </div>

      {error && <p className="rounded bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

      {voices.length === 0 ? (
        <p className="text-sm text-slate-500">No voices defined yet - create one in the Voices section.</p>
      ) : (
        <div className="flex flex-wrap items-end gap-3 rounded-lg border border-slate-200 bg-slate-50 p-3">
          <div className="flex flex-col gap-1">
            <label htmlFor={`voice-select-${track}`} className="text-xs font-medium text-slate-600">
              Voice
            </label>
            <select
              id={`voice-select-${track}`}
              value={selectedVoiceId}
              onChange={(e) => setSelectedVoiceId(e.target.value)}
              className="w-56 rounded border border-slate-300 px-3 py-1.5 text-sm"
            >
              {voices.map((voice) => (
                <option key={voice.id} value={voice.id}>
                  {voice.name}
                  {voice.is_default ? " (default)" : ""}
                </option>
              ))}
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label htmlFor={`voice-seed-${track}`} className="text-xs font-medium text-slate-600">
              Seed (optional)
            </label>
            <input
              id={`voice-seed-${track}`}
              type="number"
              value={seed}
              onChange={(e) => setSeed(e.target.value)}
              placeholder="random"
              className="w-32 rounded border border-slate-300 px-3 py-1.5 text-sm"
            />
          </div>
          <button
            onClick={handleGenerate}
            disabled={generating || !text || !selectedVoiceId}
            className="rounded bg-slate-900 px-4 py-1.5 text-sm font-medium text-white disabled:opacity-50"
          >
            {generating ? "Generating..." : `Generate ${label} Audio`}
          </button>
        </div>
      )}

      {loading ? (
        <p className="text-sm text-slate-500">Loading versions...</p>
      ) : (
        <GenerationGallery
          generations={generations}
          busyId={busyId}
          emptyMessage={`No ${label.toLowerCase()} audio versions yet.`}
          onApprove={(id) => runAction(id, approveGeneration)}
          onReject={(id) => runAction(id, rejectGeneration)}
          onActivate={(id) => runAction(id, activateGeneration)}
          onDelete={handleDelete}
          renderPreview={(generation) => (
            <div className="flex items-center justify-center bg-slate-50 p-3">
              {generation.output_path ? (
                // eslint-disable-next-line jsx-a11y/media-has-caption
                <audio controls src={mediaUrl(generation.output_path)} className="w-full" />
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

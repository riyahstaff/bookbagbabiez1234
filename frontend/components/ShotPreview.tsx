"use client";

import { useRef } from "react";
import { mediaUrl } from "@/lib/api";
import type { Generation, Shot } from "@/lib/types";

function isAnimatedImage(path: string): boolean {
  return path.toLowerCase().endsWith(".gif");
}

function qcSummary(generations: (Generation | null)[]): string {
  const present = generations.filter((g): g is Generation => g !== null && g.quality_score !== null);
  if (present.length === 0) return "No automated QC results yet - generate something above.";
  const flagged = present.filter((g) => (g.quality_score ?? 1) < 0.8);
  if (flagged.length === 0) return `All ${present.length} active generation(s) passed automated QC.`;
  return `${flagged.length} of ${present.length} active generation(s) flagged by automated QC - see notes below.`;
}

interface ShotPreviewProps {
  shot: Shot;
}

export default function ShotPreview({ shot }: ShotPreviewProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const dialogueRef = useRef<HTMLAudioElement>(null);
  const narrationRef = useRef<HTMLAudioElement>(null);

  const visual = shot.active_video_generation ?? shot.active_image_generation;
  const visualIsRealVideo =
    !!shot.active_video_generation && !!visual?.output_path && !isAnimatedImage(visual.output_path);

  const activeGenerations = [
    shot.active_image_generation,
    shot.active_dialogue_generation,
    shot.active_narration_generation,
    shot.active_video_generation,
  ];
  const flagged = activeGenerations.filter(
    (g): g is Generation => !!g && g.quality_score !== null && g.quality_score < 0.8,
  );

  function handlePlayAll() {
    videoRef.current?.play().catch(() => {});
    dialogueRef.current?.play().catch(() => {});
    narrationRef.current?.play().catch(() => {});
  }

  return (
    <section className="space-y-3 rounded-lg border border-slate-200 bg-white p-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-medium">Shot Preview</h2>
          <p className="text-sm text-slate-500">
            A quick look at this shot&apos;s active pieces together for review - not a synced final
            export, that&apos;s the episode assembler.
          </p>
        </div>
        <button
          onClick={handlePlayAll}
          className="rounded border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50"
        >
          Play All
        </button>
      </div>

      <div className="flex aspect-video items-center justify-center overflow-hidden rounded bg-slate-100">
        {visual?.output_path ? (
          visualIsRealVideo ? (
            // eslint-disable-next-line jsx-a11y/media-has-caption
            <video
              ref={videoRef}
              controls
              src={mediaUrl(visual.output_path)}
              className="h-full w-full object-contain"
            />
          ) : (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={mediaUrl(visual.output_path)}
              alt="Shot preview"
              className="h-full w-full object-contain"
            />
          )
        ) : (
          <span className="text-sm text-slate-400">No image or video generated yet.</span>
        )}
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div>
          <p className="text-xs font-medium text-slate-600">Dialogue</p>
          {shot.active_dialogue_generation?.output_path ? (
            // eslint-disable-next-line jsx-a11y/media-has-caption
            <audio
              ref={dialogueRef}
              controls
              src={mediaUrl(shot.active_dialogue_generation.output_path)}
              className="w-full"
            />
          ) : (
            <p className="text-sm text-slate-400">Not generated yet.</p>
          )}
        </div>
        <div>
          <p className="text-xs font-medium text-slate-600">Narration</p>
          {shot.active_narration_generation?.output_path ? (
            // eslint-disable-next-line jsx-a11y/media-has-caption
            <audio
              ref={narrationRef}
              controls
              src={mediaUrl(shot.active_narration_generation.output_path)}
              className="w-full"
            />
          ) : (
            <p className="text-sm text-slate-400">Not generated yet.</p>
          )}
        </div>
      </div>

      <p className="rounded bg-slate-50 px-3 py-2 text-sm text-slate-600">{qcSummary(activeGenerations)}</p>
      {flagged.length > 0 && (
        <ul className="space-y-1 text-xs text-amber-700">
          {flagged.map((generation) => (
            <li key={generation.id}>{generation.qc_notes}</li>
          ))}
        </ul>
      )}
    </section>
  );
}

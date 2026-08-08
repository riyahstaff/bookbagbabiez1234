"use client";

import { useEffect, useState } from "react";
import {
  createEpisodeExport,
  deleteEpisodeExport,
  listEpisodeExports,
  mediaUrl,
  previewEpisodeExport,
} from "@/lib/api";
import type { EpisodeExport, EpisodeExportOptions, EpisodeExportPreview } from "@/lib/types";

const STATUS_COLORS: Record<EpisodeExport["status"], string> = {
  QUEUED: "bg-slate-100 text-slate-600",
  PREPARING: "bg-slate-100 text-slate-600",
  RUNNING: "bg-blue-100 text-blue-700",
  PROCESSING: "bg-blue-100 text-blue-700",
  COMPLETE: "bg-green-100 text-green-700",
  FAILED: "bg-red-100 text-red-700",
  CANCELED: "bg-slate-100 text-slate-600",
};

function formatDuration(seconds: number | null): string {
  if (seconds === null) return "-";
  const total = Math.round(seconds);
  const minutes = Math.floor(total / 60);
  const remainder = total % 60;
  return `${minutes}:${remainder.toString().padStart(2, "0")}`;
}

interface EpisodeExportPanelProps {
  episodeId: number;
  onEpisodeChanged?: () => void;
}

export default function EpisodeExportPanel({ episodeId, onEpisodeChanged }: EpisodeExportPanelProps) {
  const [preview, setPreview] = useState<EpisodeExportPreview | null>(null);
  const [exports, setExports] = useState<EpisodeExport[]>([]);
  const [options, setOptions] = useState<EpisodeExportOptions>({
    include_titles: true,
    include_credits: true,
    include_subtitles: true,
  });
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  function refresh() {
    return Promise.all([previewEpisodeExport(episodeId), listEpisodeExports(episodeId)]).then(
      ([previewData, exportsData]) => {
        setPreview(previewData);
        setExports(exportsData);
      },
    );
  }

  useEffect(() => {
    refresh()
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load export data"))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [episodeId]);

  function toggleOption(key: keyof EpisodeExportOptions) {
    setOptions((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  async function handleExport() {
    setExporting(true);
    setError(null);
    try {
      await createEpisodeExport(episodeId, options);
      await refresh();
      onEpisodeChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to export episode");
    } finally {
      setExporting(false);
    }
  }

  async function handleDelete(exportId: number) {
    if (!confirm("Delete this export? The rendered video file will be removed.")) return;
    setBusyId(exportId);
    setError(null);
    try {
      await deleteEpisodeExport(exportId);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete export");
    } finally {
      setBusyId(null);
    }
  }

  const canExport = !loading && !exporting && (preview?.renderable_shot_count ?? 0) > 0;

  return (
    <section className="space-y-3 rounded-lg border border-slate-200 bg-white p-4">
      <div>
        <h2 className="text-lg font-medium">Export</h2>
        <p className="text-sm text-slate-500">
          Assembles every shot&apos;s active video (or held image) with its mixed dialogue/narration audio
          into a single episode file, via ffmpeg.
        </p>
      </div>

      {error && <p className="rounded bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

      {loading ? (
        <p className="text-sm text-slate-500">Loading...</p>
      ) : (
        <>
          {preview && preview.renderable_shot_count === 0 && (
            <p className="rounded bg-amber-50 px-3 py-2 text-sm text-amber-700">
              No shots have an approved image or activated video yet - nothing to export.
            </p>
          )}
          {preview && preview.skipped_shots.length > 0 && (
            <p className="rounded bg-amber-50 px-3 py-2 text-sm text-amber-700">
              {preview.renderable_shot_count > 0
                ? `${preview.renderable_shot_count} shot(s) will be included. `
                : ""}
              The following shot(s) have no renderable image/video and will be skipped:{" "}
              {preview.skipped_shots.join(", ")}
            </p>
          )}

          <div className="flex flex-wrap items-end gap-4 rounded-lg border border-slate-200 bg-slate-50 p-3">
            <div className="flex flex-wrap gap-4">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={options.include_titles}
                  onChange={() => toggleOption("include_titles")}
                  className="h-4 w-4"
                />
                Title card
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={options.include_credits}
                  onChange={() => toggleOption("include_credits")}
                  className="h-4 w-4"
                />
                Credits card
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={options.include_subtitles}
                  onChange={() => toggleOption("include_subtitles")}
                  className="h-4 w-4"
                />
                Subtitles
              </label>
            </div>
            <button
              onClick={handleExport}
              disabled={!canExport}
              className="rounded bg-slate-900 px-4 py-1.5 text-sm font-medium text-white disabled:opacity-50"
            >
              {exporting ? "Exporting..." : "Export Episode"}
            </button>
          </div>

          {exports.length === 0 ? (
            <p className="text-sm text-slate-500">No exports yet.</p>
          ) : (
            <ul className="space-y-3">
              {exports.map((exp) => (
                <li key={exp.id} className="space-y-2 rounded-lg border border-slate-200 p-3">
                  <div className="flex flex-wrap items-center gap-2 text-xs">
                    <span className={`rounded px-1.5 py-0.5 font-medium ${STATUS_COLORS[exp.status]}`}>
                      {exp.status}
                    </span>
                    <span className="text-slate-500">{formatDuration(exp.duration_seconds)}</span>
                    <span className="text-slate-400">
                      {[
                        exp.include_titles && "titles",
                        exp.include_credits && "credits",
                        exp.include_subtitles && "subtitles",
                      ]
                        .filter(Boolean)
                        .join(" + ") || "no extras"}
                    </span>
                    <span className="text-slate-400">{new Date(exp.created_at).toLocaleString()}</span>
                    <button
                      onClick={() => handleDelete(exp.id)}
                      disabled={busyId === exp.id}
                      className="ml-auto rounded border border-slate-300 px-2 py-1 text-slate-500 hover:bg-slate-50 disabled:opacity-50"
                    >
                      Delete
                    </button>
                  </div>

                  {exp.status === "FAILED" && exp.error_message && (
                    <p className="text-xs text-red-700">{exp.error_message}</p>
                  )}

                  {exp.skipped_shots && exp.skipped_shots.length > 0 && (
                    <p className="text-xs text-amber-700">Skipped: {exp.skipped_shots.join(", ")}</p>
                  )}

                  {exp.status === "COMPLETE" && exp.output_path && (
                    <div className="space-y-1">
                      {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
                      <video controls src={mediaUrl(exp.output_path)} className="w-full max-w-lg rounded" />
                      <a
                        href={mediaUrl(exp.output_path)}
                        download
                        className="text-xs text-slate-500 hover:underline"
                      >
                        Download
                      </a>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </section>
  );
}

"use client";

import type { ReactNode } from "react";
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

interface GenerationGalleryProps {
  generations: Generation[];
  busyId: number | null;
  emptyMessage: string;
  renderPreview: (generation: Generation) => ReactNode;
  onApprove: (generationId: number) => void;
  onReject: (generationId: number) => void;
  onActivate: (generationId: number) => void;
  onDelete: (generationId: number) => void;
}

export default function GenerationGallery({
  generations,
  busyId,
  emptyMessage,
  renderPreview,
  onApprove,
  onReject,
  onActivate,
  onDelete,
}: GenerationGalleryProps) {
  if (generations.length === 0) {
    return <p className="text-sm text-slate-500">{emptyMessage}</p>;
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {generations.map((generation) => (
        <div
          key={generation.id}
          className={`overflow-hidden rounded-lg border bg-white ${
            generation.is_active ? "border-slate-900 ring-1 ring-slate-900" : "border-slate-200"
          }`}
        >
          {renderPreview(generation)}
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
              {generation.seed !== null && <span className="text-slate-500">seed={generation.seed}</span>}
            </div>
            <div className="flex flex-wrap gap-1.5">
              <button
                onClick={() => onApprove(generation.id)}
                disabled={busyId === generation.id || generation.approval_status === "APPROVED"}
                className="rounded border border-green-200 px-2 py-1 text-xs text-green-700 hover:bg-green-50 disabled:opacity-50"
              >
                Approve
              </button>
              <button
                onClick={() => onReject(generation.id)}
                disabled={busyId === generation.id || generation.approval_status === "REJECTED"}
                className="rounded border border-red-200 px-2 py-1 text-xs text-red-700 hover:bg-red-50 disabled:opacity-50"
              >
                Reject
              </button>
              <button
                onClick={() => onActivate(generation.id)}
                disabled={busyId === generation.id || generation.is_active}
                className="rounded border border-slate-300 px-2 py-1 text-xs hover:bg-slate-50 disabled:opacity-50"
              >
                Activate
              </button>
              <button
                onClick={() => onDelete(generation.id)}
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
  );
}

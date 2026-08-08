"use client";

import { useState } from "react";

export interface ReferenceItem {
  id: number;
  imageUrl: string;
  tag: string | null;
}

interface ReferenceGalleryProps {
  items: ReferenceItem[];
  tagLabel: string;
  categories?: string[];
  onUpload: (file: File, tag: string) => Promise<void>;
  onDelete: (id: number) => Promise<void>;
}

export default function ReferenceGallery({
  items,
  tagLabel,
  categories,
  onUpload,
  onDelete,
}: ReferenceGalleryProps) {
  const [file, setFile] = useState<File | null>(null);
  const [tag, setTag] = useState(categories?.[0] ?? "");
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      await onUpload(file, tag);
      setFile(null);
      const input = document.getElementById(`file-${tagLabel}`) as HTMLInputElement | null;
      if (input) input.value = "";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="space-y-3">
      {error && <p className="rounded bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

      <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-3 rounded-lg border border-slate-200 bg-white p-3">
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-slate-600">{tagLabel}</label>
          {categories ? (
            <select
              className="rounded border border-slate-300 px-3 py-1.5 text-sm"
              value={tag}
              onChange={(e) => setTag(e.target.value)}
            >
              {categories.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          ) : (
            <input
              className="rounded border border-slate-300 px-3 py-1.5 text-sm"
              value={tag}
              onChange={(e) => setTag(e.target.value)}
              placeholder="optional label"
            />
          )}
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-slate-600">Image file</label>
          <input
            id={`file-${tagLabel}`}
            type="file"
            accept="image/*"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="text-sm"
          />
        </div>
        <button
          type="submit"
          disabled={uploading || !file}
          className="rounded bg-slate-900 px-4 py-1.5 text-sm font-medium text-white disabled:opacity-50"
        >
          {uploading ? "Uploading..." : "Upload"}
        </button>
      </form>

      {items.length === 0 ? (
        <p className="text-sm text-slate-500">No reference images yet.</p>
      ) : (
        <div className="grid grid-cols-3 gap-3 sm:grid-cols-4 md:grid-cols-6">
          {items.map((item) => (
            <div key={item.id} className="group relative overflow-hidden rounded-lg border border-slate-200 bg-white">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={item.imageUrl} alt={item.tag ?? "reference"} className="h-28 w-full object-cover" />
              <p className="truncate px-1.5 py-1 text-[11px] font-medium text-slate-600">{item.tag}</p>
              <button
                type="button"
                onClick={() => onDelete(item.id)}
                className="absolute right-1 top-1 hidden rounded bg-white/90 px-1.5 py-0.5 text-[11px] text-red-700 group-hover:block"
              >
                Delete
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

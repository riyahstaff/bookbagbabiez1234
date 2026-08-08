"use client";

import { useEffect, useState } from "react";
import {
  deleteOutfitReference,
  listOutfitReferences,
  mediaUrl,
  uploadOutfitReference,
} from "@/lib/api";
import type { CharacterOutfit, OutfitReference } from "@/lib/types";
import ReferenceGallery from "@/components/ReferenceGallery";

export default function OutfitCard({
  outfit,
  onDelete,
}: {
  outfit: CharacterOutfit;
  onDelete: (id: number) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [references, setReferences] = useState<OutfitReference[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (!expanded || loaded) return;
    listOutfitReferences(outfit.id).then((data) => {
      setReferences(data);
      setLoaded(true);
    });
  }, [expanded, loaded, outfit.id]);

  async function refresh() {
    setReferences(await listOutfitReferences(outfit.id));
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white">
      <div className="flex items-center justify-between px-4 py-3">
        <div>
          <p className="font-medium">{outfit.name}</p>
          <p className="text-xs text-slate-500">
            {outfit.outfit_code}
            {outfit.description ? ` · ${outfit.description}` : ""}
          </p>
        </div>
        <div className="flex gap-3 text-sm">
          <button onClick={() => setExpanded((v) => !v)} className="text-slate-500 hover:underline">
            {expanded ? "Hide references" : "Show references"}
          </button>
          <button onClick={() => onDelete(outfit.id)} className="text-red-700 hover:underline">
            Delete
          </button>
        </div>
      </div>
      {expanded && (
        <div className="border-t border-slate-100 p-3">
          <ReferenceGallery
            tagLabel="Label"
            items={references.map((r) => ({ id: r.id, imageUrl: mediaUrl(r.image_path), tag: r.label }))}
            onUpload={async (file, label) => {
              await uploadOutfitReference(outfit.id, file, label || undefined);
              await refresh();
            }}
            onDelete={async (id) => {
              await deleteOutfitReference(id);
              await refresh();
            }}
          />
        </div>
      )}
    </div>
  );
}

export interface Series {
  id: number;
  series_code: string;
  title: string;
  description: string | null;
  genre: string | null;
  animation_style: string | null;
  target_resolution: string;
  default_fps: number;
  target_episode_length_minutes: number;
  aspect_ratio: string;
  visual_style_prompt: string | null;
  negative_style_prompt: string | null;
  default_voice_settings: string | null;
  default_video_provider: string | null;
  default_image_provider: string | null;
  created_at: string;
  updated_at: string;
}

export type SeriesInput = Partial<
  Omit<Series, "id" | "series_code" | "created_at" | "updated_at">
>;

export interface Character {
  id: number;
  series_id: number;
  character_code: string;
  name: string;
  description: string | null;
  age_range: string | null;
  height: string | null;
  build: string | null;
  skin_tone: string | null;
  hair: string | null;
  facial_features: string | null;
  clothing: string | null;
  accessories: string | null;
  personality: string | null;
  movement_style: string | null;
  speaking_style: string | null;
  accent: string | null;
  visual_style_notes: string | null;
  continuity_restrictions: string | null;
  created_at: string;
  updated_at: string;
}

export type CharacterInput = Partial<
  Omit<Character, "id" | "series_id" | "character_code" | "created_at" | "updated_at">
>;

export type EpisodeStatus =
  | "DRAFT"
  | "SCRIPT_READY"
  | "SCENES_READY"
  | "STORYBOARD_READY"
  | "RENDERING"
  | "QC"
  | "COMPLETE";

export const EPISODE_STATUSES: EpisodeStatus[] = [
  "DRAFT",
  "SCRIPT_READY",
  "SCENES_READY",
  "STORYBOARD_READY",
  "RENDERING",
  "QC",
  "COMPLETE",
];

export interface Episode {
  id: number;
  series_id: number;
  episode_code: string;
  episode_number: number;
  title: string;
  summary: string | null;
  treatment: string | null;
  script: string | null;
  narration: string | null;
  target_runtime_seconds: number | null;
  current_estimated_runtime_seconds: number | null;
  status: EpisodeStatus;
  created_at: string;
  updated_at: string;
}

export type EpisodeInput = Partial<
  Omit<Episode, "id" | "series_id" | "episode_code" | "status" | "created_at" | "updated_at">
>;

export type ProviderCapability =
  | "VIDEO"
  | "VOICE"
  | "IMAGE"
  | "LLM"
  | "UPSCALE"
  | "LIPSYNC"
  | "COMPUTE";

export const PROVIDER_CAPABILITIES: ProviderCapability[] = [
  "VIDEO",
  "VOICE",
  "IMAGE",
  "LLM",
  "UPSCALE",
  "LIPSYNC",
  "COMPUTE",
];

export interface ProviderConfiguration {
  id: number;
  capability: string;
  provider_name: string;
  is_default: boolean;
  config: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectSetting {
  id: number;
  key: string;
  value: string | null;
  updated_at: string;
}

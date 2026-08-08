export interface Series {
  id: number;
  series_code: string;
  title: string;
  description: string | null;
  world_details: string | null;
  continuity_rules: string | null;
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
  outline: string | null;
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

export type CharacterReferenceCategory =
  | "FRONT"
  | "SIDE"
  | "THREE_QUARTER"
  | "FULL_BODY"
  | "CLOSE_UP"
  | "HAPPY"
  | "ANGRY"
  | "SAD"
  | "TALKING"
  | "SITTING"
  | "WALKING"
  | "RUNNING"
  | "ADDITIONAL";

export const CHARACTER_REFERENCE_CATEGORIES: CharacterReferenceCategory[] = [
  "FRONT",
  "SIDE",
  "THREE_QUARTER",
  "FULL_BODY",
  "CLOSE_UP",
  "HAPPY",
  "ANGRY",
  "SAD",
  "TALKING",
  "SITTING",
  "WALKING",
  "RUNNING",
  "ADDITIONAL",
];

export interface CharacterReference {
  id: number;
  character_id: number;
  category: CharacterReferenceCategory;
  image_path: string;
  notes: string | null;
  created_at: string;
}

export interface CharacterOutfit {
  id: number;
  character_id: number;
  outfit_code: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface OutfitReference {
  id: number;
  outfit_id: number;
  label: string | null;
  image_path: string;
  notes: string | null;
  created_at: string;
}

export interface Voice {
  id: number;
  series_id: number;
  character_id: number | null;
  voice_code: string;
  name: string;
  provider: string | null;
  provider_voice_id: string | null;
  reference_audio_path: string | null;
  description: string | null;
  speaking_style: string | null;
  speed: number | null;
  pitch: number | null;
  emotion: string | null;
  generation_settings: Record<string, unknown> | null;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export type VoiceInput = Partial<
  Omit<Voice, "id" | "series_id" | "voice_code" | "reference_audio_path" | "created_at" | "updated_at">
>;

export type LocationReferenceCategory =
  | "WIDE_ESTABLISHING"
  | "MEDIUM"
  | "CLOSE_BACKGROUND"
  | "INTERIOR_NORTH"
  | "INTERIOR_SOUTH"
  | "INTERIOR_EAST"
  | "INTERIOR_WEST"
  | "ADDITIONAL";

export const LOCATION_REFERENCE_CATEGORIES: LocationReferenceCategory[] = [
  "WIDE_ESTABLISHING",
  "MEDIUM",
  "CLOSE_BACKGROUND",
  "INTERIOR_NORTH",
  "INTERIOR_SOUTH",
  "INTERIOR_EAST",
  "INTERIOR_WEST",
  "ADDITIONAL",
];

export interface Location {
  id: number;
  series_id: number;
  location_code: string;
  name: string;
  description: string | null;
  lighting_notes: string | null;
  time_of_day_notes: string | null;
  camera_reference_notes: string | null;
  important_props: string | null;
  continuity_rules: string | null;
  created_at: string;
  updated_at: string;
}

export type LocationInput = Partial<
  Omit<Location, "id" | "series_id" | "location_code" | "created_at" | "updated_at">
>;

export interface LocationReference {
  id: number;
  location_id: number;
  category: LocationReferenceCategory;
  image_path: string;
  notes: string | null;
  created_at: string;
}

export interface Prop {
  id: number;
  series_id: number;
  prop_code: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export type PropInput = Partial<Omit<Prop, "id" | "series_id" | "prop_code" | "created_at" | "updated_at">>;

export interface PropReference {
  id: number;
  prop_id: number;
  label: string | null;
  image_path: string;
  notes: string | null;
  created_at: string;
}

export type SceneStatus = "DRAFT" | "SHOTS_READY";

export interface SceneCharacterAssignment {
  character_id: number;
  outfit_id: number | null;
}

export interface Scene {
  id: number;
  episode_id: number;
  scene_number: number;
  location_id: number | null;
  time_of_day: string | null;
  action_description: string | null;
  dialogue: string | null;
  narration: string | null;
  emotional_tone: string | null;
  continuity_notes: string | null;
  estimated_duration_seconds: number | null;
  status: SceneStatus;
  characters: SceneCharacterAssignment[];
  created_at: string;
  updated_at: string;
}

export type SceneInput = Partial<
  Omit<Scene, "id" | "episode_id" | "status" | "characters" | "created_at" | "updated_at">
>;

export type ShotType =
  | "ESTABLISHING"
  | "EXTREME_WIDE"
  | "WIDE"
  | "MEDIUM"
  | "MEDIUM_CLOSE_UP"
  | "CLOSE_UP"
  | "EXTREME_CLOSE_UP"
  | "OVER_THE_SHOULDER"
  | "TWO_SHOT"
  | "REACTION_SHOT"
  | "INSERT_SHOT"
  | "POV"
  | "TRACKING"
  | "PAN"
  | "TILT"
  | "STATIC";

export const SHOT_TYPES: ShotType[] = [
  "ESTABLISHING",
  "EXTREME_WIDE",
  "WIDE",
  "MEDIUM",
  "MEDIUM_CLOSE_UP",
  "CLOSE_UP",
  "EXTREME_CLOSE_UP",
  "OVER_THE_SHOULDER",
  "TWO_SHOT",
  "REACTION_SHOT",
  "INSERT_SHOT",
  "POV",
  "TRACKING",
  "PAN",
  "TILT",
  "STATIC",
];

export interface ShotCharacterAssignment {
  character_id: number;
  outfit_id: number | null;
}

export type GenerationType = "IMAGE" | "VOICE" | "VIDEO";

export type AudioTrack = "DIALOGUE" | "NARRATION";

export type GenerationStatus =
  | "QUEUED"
  | "PREPARING"
  | "RUNNING"
  | "PROCESSING"
  | "COMPLETE"
  | "FAILED"
  | "CANCELED";

export type ApprovalStatus = "PENDING" | "APPROVED" | "REJECTED";

export interface Generation {
  id: number;
  shot_id: number;
  generation_type: GenerationType;
  audio_track: AudioTrack | null;
  voice_id: number | null;
  provider_name: string;
  model_name: string | null;
  workflow_version: string | null;
  prompt: string | null;
  negative_prompt: string | null;
  seed: number | null;
  generation_settings: Record<string, unknown> | null;
  status: GenerationStatus;
  error_message: string | null;
  output_path: string | null;
  preview_path: string | null;
  quality_score: number | null;
  approval_status: ApprovalStatus;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Shot {
  id: number;
  scene_id: number;
  shot_number: number;
  shot_type: ShotType;
  camera_angle: string | null;
  camera_movement: string | null;
  action: string | null;
  dialogue: string | null;
  narration: string | null;
  emotion: string | null;
  lighting: string | null;
  duration_seconds: number | null;
  visual_prompt: string | null;
  negative_prompt: string | null;
  characters: ShotCharacterAssignment[];
  active_image_generation: Generation | null;
  active_dialogue_generation: Generation | null;
  active_narration_generation: Generation | null;
  created_at: string;
  updated_at: string;
}

export type ShotInput = Partial<
  Omit<
    Shot,
    | "id"
    | "scene_id"
    | "characters"
    | "active_image_generation"
    | "active_dialogue_generation"
    | "active_narration_generation"
    | "created_at"
    | "updated_at"
  >
>;

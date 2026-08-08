import type {
  Character,
  CharacterInput,
  CharacterOutfit,
  CharacterReference,
  CharacterReferenceCategory,
  Episode,
  EpisodeInput,
  EpisodeStatus,
  Generation,
  Location,
  LocationInput,
  LocationReference,
  LocationReferenceCategory,
  OutfitReference,
  ProjectSetting,
  Prop,
  PropInput,
  PropReference,
  ProviderCapability,
  ProviderConfiguration,
  Scene,
  SceneCharacterAssignment,
  SceneInput,
  Series,
  SeriesInput,
  Shot,
  ShotCharacterAssignment,
  ShotInput,
  Voice,
  VoiceInput,
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export const mediaUrl = (relativePath: string) => `${API_BASE_URL}/media/${relativePath}`;

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const raw = await response.text();
    let message = raw;
    try {
      const parsed = JSON.parse(raw);
      message = typeof parsed.detail === "string" ? parsed.detail : JSON.stringify(parsed.detail ?? parsed);
    } catch {
      // response wasn't JSON - fall back to raw text
    }
    throw new ApiError(response.status, message || `Request failed with status ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  return handleResponse<T>(response);
}

async function uploadRequest<T>(path: string, formData: FormData): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, { method: "POST", body: formData });
  return handleResponse<T>(response);
}

// Series
export const listSeries = () => request<Series[]>("/api/series");
export const getSeries = (id: number) => request<Series>(`/api/series/${id}`);
export const createSeries = (input: SeriesInput) =>
  request<Series>("/api/series", { method: "POST", body: JSON.stringify(input) });
export const updateSeries = (id: number, input: SeriesInput) =>
  request<Series>(`/api/series/${id}`, { method: "PATCH", body: JSON.stringify(input) });
export const deleteSeries = (id: number) => request<void>(`/api/series/${id}`, { method: "DELETE" });

// Characters
export const listCharacters = (seriesId: number) =>
  request<Character[]>(`/api/series/${seriesId}/characters`);
export const getCharacter = (id: number) => request<Character>(`/api/characters/${id}`);
export const createCharacter = (seriesId: number, input: CharacterInput) =>
  request<Character>(`/api/series/${seriesId}/characters`, {
    method: "POST",
    body: JSON.stringify(input),
  });
export const updateCharacter = (id: number, input: CharacterInput) =>
  request<Character>(`/api/characters/${id}`, { method: "PATCH", body: JSON.stringify(input) });
export const deleteCharacter = (id: number) => request<void>(`/api/characters/${id}`, { method: "DELETE" });

// Episodes
export const listEpisodes = (seriesId: number) => request<Episode[]>(`/api/series/${seriesId}/episodes`);
export const getEpisode = (id: number) => request<Episode>(`/api/episodes/${id}`);
export const createEpisode = (seriesId: number, input: EpisodeInput & { episode_number: number; title: string }) =>
  request<Episode>(`/api/series/${seriesId}/episodes`, {
    method: "POST",
    body: JSON.stringify(input),
  });
export const updateEpisode = (id: number, input: EpisodeInput & { status?: EpisodeStatus }) =>
  request<Episode>(`/api/episodes/${id}`, { method: "PATCH", body: JSON.stringify(input) });
export const deleteEpisode = (id: number) => request<void>(`/api/episodes/${id}`, { method: "DELETE" });

// Settings
export const listProjectSettings = () => request<ProjectSetting[]>("/api/settings/project");
export const upsertProjectSetting = (key: string, value: string | null) =>
  request<ProjectSetting>("/api/settings/project", {
    method: "PUT",
    body: JSON.stringify({ key, value }),
  });

export const listProviderConfigurations = () =>
  request<ProviderConfiguration[]>("/api/settings/providers");
export const createProviderConfiguration = (input: {
  capability: ProviderCapability;
  provider_name: string;
  is_default?: boolean;
  config?: Record<string, unknown> | null;
}) =>
  request<ProviderConfiguration>("/api/settings/providers", {
    method: "POST",
    body: JSON.stringify(input),
  });
export const updateProviderConfiguration = (
  id: number,
  input: Partial<{ provider_name: string; is_default: boolean; config: Record<string, unknown> | null }>,
) =>
  request<ProviderConfiguration>(`/api/settings/providers/${id}`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
export const deleteProviderConfiguration = (id: number) =>
  request<void>(`/api/settings/providers/${id}`, { method: "DELETE" });

// Character references
export const listCharacterReferences = (characterId: number) =>
  request<CharacterReference[]>(`/api/characters/${characterId}/references`);
export const uploadCharacterReference = (
  characterId: number,
  file: File,
  category: CharacterReferenceCategory,
  notes?: string,
) => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("category", category);
  if (notes) formData.append("notes", notes);
  return uploadRequest<CharacterReference>(`/api/characters/${characterId}/references`, formData);
};
export const deleteCharacterReference = (referenceId: number) =>
  request<void>(`/api/character-references/${referenceId}`, { method: "DELETE" });

// Character outfits
export const listOutfits = (characterId: number) =>
  request<CharacterOutfit[]>(`/api/characters/${characterId}/outfits`);
export const createOutfit = (characterId: number, name: string, description?: string) =>
  request<CharacterOutfit>(`/api/characters/${characterId}/outfits`, {
    method: "POST",
    body: JSON.stringify({ name, description: description || null }),
  });
export const deleteOutfit = (outfitId: number) =>
  request<void>(`/api/character-outfits/${outfitId}`, { method: "DELETE" });

export const listOutfitReferences = (outfitId: number) =>
  request<OutfitReference[]>(`/api/character-outfits/${outfitId}/references`);
export const uploadOutfitReference = (outfitId: number, file: File, label?: string, notes?: string) => {
  const formData = new FormData();
  formData.append("file", file);
  if (label) formData.append("label", label);
  if (notes) formData.append("notes", notes);
  return uploadRequest<OutfitReference>(`/api/character-outfits/${outfitId}/references`, formData);
};
export const deleteOutfitReference = (referenceId: number) =>
  request<void>(`/api/outfit-references/${referenceId}`, { method: "DELETE" });

// Voices
export const listVoices = (seriesId: number) => request<Voice[]>(`/api/series/${seriesId}/voices`);
export const createVoice = (seriesId: number, input: VoiceInput & { name: string }) =>
  request<Voice>(`/api/series/${seriesId}/voices`, { method: "POST", body: JSON.stringify(input) });
export const updateVoice = (id: number, input: VoiceInput) =>
  request<Voice>(`/api/voices/${id}`, { method: "PATCH", body: JSON.stringify(input) });
export const deleteVoice = (id: number) => request<void>(`/api/voices/${id}`, { method: "DELETE" });
export const uploadVoiceReferenceAudio = (voiceId: number, file: File) => {
  const formData = new FormData();
  formData.append("file", file);
  return uploadRequest<Voice>(`/api/voices/${voiceId}/reference-audio`, formData);
};

// Locations
export const listLocations = (seriesId: number) => request<Location[]>(`/api/series/${seriesId}/locations`);
export const getLocation = (id: number) => request<Location>(`/api/locations/${id}`);
export const createLocation = (seriesId: number, input: LocationInput & { name: string }) =>
  request<Location>(`/api/series/${seriesId}/locations`, { method: "POST", body: JSON.stringify(input) });
export const updateLocation = (id: number, input: LocationInput) =>
  request<Location>(`/api/locations/${id}`, { method: "PATCH", body: JSON.stringify(input) });
export const deleteLocation = (id: number) => request<void>(`/api/locations/${id}`, { method: "DELETE" });

export const listLocationReferences = (locationId: number) =>
  request<LocationReference[]>(`/api/locations/${locationId}/references`);
export const uploadLocationReference = (
  locationId: number,
  file: File,
  category: LocationReferenceCategory,
  notes?: string,
) => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("category", category);
  if (notes) formData.append("notes", notes);
  return uploadRequest<LocationReference>(`/api/locations/${locationId}/references`, formData);
};
export const deleteLocationReference = (referenceId: number) =>
  request<void>(`/api/location-references/${referenceId}`, { method: "DELETE" });

// Props
export const listProps = (seriesId: number) => request<Prop[]>(`/api/series/${seriesId}/props`);
export const getProp = (id: number) => request<Prop>(`/api/props/${id}`);
export const createProp = (seriesId: number, input: PropInput & { name: string }) =>
  request<Prop>(`/api/series/${seriesId}/props`, { method: "POST", body: JSON.stringify(input) });
export const updateProp = (id: number, input: PropInput) =>
  request<Prop>(`/api/props/${id}`, { method: "PATCH", body: JSON.stringify(input) });
export const deleteProp = (id: number) => request<void>(`/api/props/${id}`, { method: "DELETE" });

export const listPropReferences = (propId: number) =>
  request<PropReference[]>(`/api/props/${propId}/references`);
export const uploadPropReference = (propId: number, file: File, label?: string, notes?: string) => {
  const formData = new FormData();
  formData.append("file", file);
  if (label) formData.append("label", label);
  if (notes) formData.append("notes", notes);
  return uploadRequest<PropReference>(`/api/props/${propId}/references`, formData);
};
export const deletePropReference = (referenceId: number) =>
  request<void>(`/api/prop-references/${referenceId}`, { method: "DELETE" });

// Episode story-pipeline actions
export const generateEpisodeOutline = (episodeId: number) =>
  request<Episode>(`/api/episodes/${episodeId}/generate-outline`, { method: "POST" });
export const generateEpisodeScript = (episodeId: number) =>
  request<Episode>(`/api/episodes/${episodeId}/generate-script`, { method: "POST" });

// Scenes
export const listScenes = (episodeId: number) => request<Scene[]>(`/api/episodes/${episodeId}/scenes`);
export const getScene = (id: number) => request<Scene>(`/api/scenes/${id}`);
export const createScene = (episodeId: number, input: SceneInput & { scene_number: number }) =>
  request<Scene>(`/api/episodes/${episodeId}/scenes`, { method: "POST", body: JSON.stringify(input) });
export const generateScenes = (episodeId: number) =>
  request<Scene[]>(`/api/episodes/${episodeId}/generate-scenes`, { method: "POST" });
export const updateScene = (id: number, input: SceneInput) =>
  request<Scene>(`/api/scenes/${id}`, { method: "PATCH", body: JSON.stringify(input) });
export const deleteScene = (id: number) => request<void>(`/api/scenes/${id}`, { method: "DELETE" });
export const setSceneCharacters = (sceneId: number, characters: SceneCharacterAssignment[]) =>
  request<Scene>(`/api/scenes/${sceneId}/characters`, {
    method: "PUT",
    body: JSON.stringify({ characters }),
  });

// Shots
export const listShots = (sceneId: number) => request<Shot[]>(`/api/scenes/${sceneId}/shots`);
export const getShot = (id: number) => request<Shot>(`/api/shots/${id}`);
export const createShot = (sceneId: number, input: ShotInput & { shot_number: number }) =>
  request<Shot>(`/api/scenes/${sceneId}/shots`, { method: "POST", body: JSON.stringify(input) });
export const generateShots = (sceneId: number) =>
  request<Shot[]>(`/api/scenes/${sceneId}/generate-shots`, { method: "POST" });
export const updateShot = (id: number, input: ShotInput) =>
  request<Shot>(`/api/shots/${id}`, { method: "PATCH", body: JSON.stringify(input) });
export const deleteShot = (id: number) => request<void>(`/api/shots/${id}`, { method: "DELETE" });
export const setShotCharacters = (shotId: number, characters: ShotCharacterAssignment[]) =>
  request<Shot>(`/api/shots/${shotId}/characters`, {
    method: "PUT",
    body: JSON.stringify({ characters }),
  });
export const buildShotPrompt = (shotId: number) =>
  request<Shot>(`/api/shots/${shotId}/build-prompt`, { method: "POST" });

// Generations (storyboard images)
export const listGenerations = (shotId: number) =>
  request<Generation[]>(`/api/shots/${shotId}/generations`);
export const generateStoryboard = (shotId: number, seed?: number | null) =>
  request<Generation>(`/api/shots/${shotId}/generate-storyboard`, {
    method: "POST",
    body: JSON.stringify({ seed: seed ?? null }),
  });
export const approveGeneration = (generationId: number) =>
  request<Generation>(`/api/generations/${generationId}/approve`, { method: "POST" });
export const rejectGeneration = (generationId: number) =>
  request<Generation>(`/api/generations/${generationId}/reject`, { method: "POST" });
export const activateGeneration = (generationId: number) =>
  request<Generation>(`/api/generations/${generationId}/activate`, { method: "POST" });
export const deleteGeneration = (generationId: number) =>
  request<void>(`/api/generations/${generationId}`, { method: "DELETE" });

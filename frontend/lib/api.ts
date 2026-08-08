import type {
  Character,
  CharacterInput,
  Episode,
  EpisodeInput,
  EpisodeStatus,
  ProjectSetting,
  ProviderCapability,
  ProviderConfiguration,
  Series,
  SeriesInput,
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

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

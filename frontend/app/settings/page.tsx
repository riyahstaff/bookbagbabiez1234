"use client";

import { useEffect, useState } from "react";
import {
  createProviderConfiguration,
  deleteProviderConfiguration,
  listProjectSettings,
  listProviderConfigurations,
  updateProviderConfiguration,
  upsertProjectSetting,
} from "@/lib/api";
import { CheckboxField, SelectField, TextField } from "@/components/Field";
import { PROVIDER_CAPABILITIES, type ProjectSetting, type ProviderCapability, type ProviderConfiguration } from "@/lib/types";

const KNOWN_SETTINGS: { key: string; label: string; hint: string }[] = [
  { key: "thrifty_mode", label: "Thrifty Mode", hint: "true / false - prefer smaller models, gate on storyboard approval, cap concurrent GPU jobs" },
  { key: "quality_mode", label: "Quality Mode", hint: "true / false - larger models, higher resolution, multiple candidates" },
];

export default function SettingsPage() {
  const [settings, setSettings] = useState<ProjectSetting[]>([]);
  const [providers, setProviders] = useState<ProviderConfiguration[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [settingValues, setSettingValues] = useState<Record<string, string>>({});

  const [capability, setCapability] = useState<ProviderCapability>("VIDEO");
  const [providerName, setProviderName] = useState("");
  const [isDefault, setIsDefault] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function refresh() {
    setLoading(true);
    try {
      const [loadedSettings, loadedProviders] = await Promise.all([
        listProjectSettings(),
        listProviderConfigurations(),
      ]);
      setSettings(loadedSettings);
      setProviders(loadedProviders);
      setSettingValues(Object.fromEntries(loadedSettings.map((s) => [s.key, s.value ?? ""])));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load settings");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function handleSaveSetting(key: string) {
    setError(null);
    try {
      await upsertProjectSetting(key, settingValues[key] ?? "");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save setting");
    }
  }

  async function handleCreateProvider(event: React.FormEvent) {
    event.preventDefault();
    if (!providerName.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      await createProviderConfiguration({ capability, provider_name: providerName, is_default: isDefault });
      setProviderName("");
      setIsDefault(false);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create provider configuration");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleToggleDefault(config: ProviderConfiguration) {
    try {
      await updateProviderConfiguration(config.id, { is_default: !config.is_default });
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update provider configuration");
    }
  }

  async function handleDeleteProvider(id: number) {
    try {
      await deleteProviderConfiguration(id);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete provider configuration");
    }
  }

  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="text-sm text-slate-500">
          Project-wide preferences and which provider handles each AI capability. Actual video/voice/image
          provider implementations arrive in later phases - this is the configuration surface for them.
        </p>
      </div>

      {error && <p className="rounded bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
      {loading && <p className="text-sm text-slate-500">Loading...</p>}

      <section className="space-y-3">
        <h2 className="text-lg font-medium">Project Settings</h2>
        <div className="space-y-3 rounded-lg border border-slate-200 bg-white p-4">
          {KNOWN_SETTINGS.map(({ key, label, hint }) => (
            <div key={key} className="flex flex-wrap items-end gap-3">
              <TextField
                label={label}
                value={settingValues[key] ?? ""}
                onChange={(e) => setSettingValues((prev) => ({ ...prev, [key]: e.target.value }))}
                placeholder="true / false"
                className="w-40"
              />
              <button
                onClick={() => handleSaveSetting(key)}
                className="rounded border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50"
                type="button"
              >
                Save
              </button>
              <p className="max-w-md text-xs text-slate-500">{hint}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-medium">Provider Configuration</h2>
        <p className="text-sm text-slate-500">
          Which provider is active for each capability. Adding a row here doesn&apos;t install anything -
          the actual providers (mock, Wan, Chatterbox, etc.) are wired up starting in Phase 3+.
        </p>

        <form
          onSubmit={handleCreateProvider}
          className="flex flex-wrap items-end gap-3 rounded-lg border border-slate-200 bg-white p-4"
        >
          <SelectField
            label="Capability"
            value={capability}
            onChange={(e) => setCapability(e.target.value as ProviderCapability)}
          >
            {PROVIDER_CAPABILITIES.map((cap) => (
              <option key={cap} value={cap}>
                {cap}
              </option>
            ))}
          </SelectField>
          <TextField
            label="Provider Name"
            value={providerName}
            onChange={(e) => setProviderName(e.target.value)}
            placeholder="mock_video"
            required
          />
          <CheckboxField label="Default for this capability" checked={isDefault} onChange={(e) => setIsDefault(e.target.checked)} />
          <button
            type="submit"
            disabled={submitting}
            className="rounded bg-slate-900 px-4 py-1.5 text-sm font-medium text-white disabled:opacity-50"
          >
            {submitting ? "Adding..." : "Add Provider"}
          </button>
        </form>

        {providers.length === 0 ? (
          <p className="text-sm text-slate-500">No provider configurations yet.</p>
        ) : (
          <ul className="divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white">
            {providers.map((provider) => (
              <li key={provider.id} className="flex items-center justify-between px-4 py-3">
                <div>
                  <p className="font-medium">
                    {provider.capability}: {provider.provider_name}
                  </p>
                  <p className="text-xs text-slate-500">{provider.is_default ? "Default" : "Alternate"}</p>
                </div>
                <div className="flex gap-3 text-sm">
                  <button onClick={() => handleToggleDefault(provider)} className="text-slate-500 hover:underline">
                    {provider.is_default ? "Unset default" : "Make default"}
                  </button>
                  <button onClick={() => handleDeleteProvider(provider.id)} className="text-red-700 hover:underline">
                    Remove
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

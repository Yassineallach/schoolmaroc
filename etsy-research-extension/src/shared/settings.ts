import { DEFAULT_SETTINGS, Settings } from './types';

const KEY = 'settings';

export async function getSettings(): Promise<Settings> {
  const r = await chrome.storage.local.get(KEY);
  const s = (r[KEY] ?? {}) as Partial<Settings>;
  return { ...DEFAULT_SETTINGS, ...s, weights: { ...DEFAULT_SETTINGS.weights, ...(s.weights ?? {}) }, fxRates: { ...(s.fxRates ?? {}) } };
}

export async function saveSettings(patch: Partial<Settings>): Promise<Settings> {
  const cur = await getSettings();
  const next = { ...cur, ...patch };
  await chrome.storage.local.set({ [KEY]: next });
  return next;
}

export function onSettingsChanged(cb: (s: Settings) => void) {
  chrome.storage.onChanged.addListener((changes, area) => {
    if (area === 'local' && changes[KEY]) getSettings().then(cb);
  });
}

import { ADMIN_FEATURE_OVERRIDE_COOKIE, ADMIN_FEATURES } from './config';

export type AdminFeatureState = 'disabled' | 'enabled' | 'inherit';

export type AdminFeatureEntry = {
  defaultEnabled: boolean;
  description: string;
  enabled: boolean;
  key: string;
  label: string;
  scope: 'admin' | 'public';
  state: AdminFeatureState;
};

function isFeatureKey(value: string): boolean {
  return ADMIN_FEATURES.some((feature) => feature.key === value);
}

export function parseFeatureOverrides(rawValue: string | undefined): Record<string, boolean> {
  if (!rawValue) return {};

  try {
    const parsed = JSON.parse(rawValue) as Record<string, unknown>;
    const next: Record<string, boolean> = {};
    for (const [key, value] of Object.entries(parsed)) {
      if (isFeatureKey(key) && typeof value === 'boolean') {
        next[key] = value;
      }
    }
    return next;
  } catch {
    return {};
  }
}

export function readFeatureOverridesFromCookies(cookies: {
  get: (name: string) => { value: string } | undefined;
}): Record<string, boolean> {
  return parseFeatureOverrides(cookies.get(ADMIN_FEATURE_OVERRIDE_COOKIE)?.value);
}

export function serializeFeatureOverrides(overrides: Record<string, boolean>): string {
  return JSON.stringify(
    Object.fromEntries(Object.entries(overrides).sort(([left], [right]) => left.localeCompare(right)))
  );
}

export function getFeatureState(key: string, overrides: Record<string, boolean>): AdminFeatureState {
  if (!(key in overrides)) return 'inherit';
  return overrides[key] ? 'enabled' : 'disabled';
}

export function isFeatureEnabled(key: string, overrides: Record<string, boolean>): boolean {
  if (key in overrides) return overrides[key];
  return ADMIN_FEATURES.find((feature) => feature.key === key)?.defaultEnabled ?? false;
}

export function getFeatureEntries(overrides: Record<string, boolean>): AdminFeatureEntry[] {
  return ADMIN_FEATURES.map((feature) => ({
    ...feature,
    enabled: isFeatureEnabled(feature.key, overrides),
    state: getFeatureState(feature.key, overrides),
  }));
}

export function collectFeatureOverridesFromFormData(formData: FormData): Record<string, boolean> {
  const next: Record<string, boolean> = {};

  for (const [key, value] of formData.entries()) {
    if (!key.startsWith('flag:') || typeof value !== 'string') continue;

    const featureKey = key.slice(5);
    if (!isFeatureKey(featureKey)) continue;

    if (value === 'enabled') next[featureKey] = true;
    if (value === 'disabled') next[featureKey] = false;
  }

  return next;
}
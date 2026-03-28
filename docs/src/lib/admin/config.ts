export const ADMIN_SESSION_COOKIE = 'agents_docs_admin_session';
export const ADMIN_CSRF_COOKIE = 'agents_docs_admin_csrf';
export const ADMIN_FEATURE_OVERRIDE_COOKIE = 'agents_docs_admin_flags';
export const ADMIN_SESSION_TTL_SECONDS = 60 * 60 * 12;
export const ADMIN_CSRF_TTL_SECONDS = 60 * 60 * 6;
export const DEV_ADMIN_PASSWORD = '41c3cf6458';

export type AdminFeatureDefinition = {
  defaultEnabled: boolean;
  description: string;
  key: string;
  label: string;
  scope: 'admin' | 'public';
};

export const ADMIN_FEATURES: AdminFeatureDefinition[] = [
  {
    key: 'telemetry_capture',
    label: 'Public telemetry capture',
    description: 'Allow browser-side docs events to be forwarded into PostHog from this browser session.',
    defaultEnabled: true,
    scope: 'public',
  },
  {
    key: 'admin_dashboard_metrics',
    label: 'Admin dashboard metrics',
    description: 'Enable the overview cards and top-content summaries in the protected admin panel.',
    defaultEnabled: true,
    scope: 'admin',
  },
  {
    key: 'admin_event_explorer',
    label: 'Admin event explorer',
    description: 'Allow querying recent telemetry events from the protected admin explorer.',
    defaultEnabled: true,
    scope: 'admin',
  },
  {
    key: 'admin_security_audit',
    label: 'Admin security audit',
    description: 'Show auth posture, recent access events, and hardening status inside the admin console.',
    defaultEnabled: true,
    scope: 'admin',
  },
  {
    key: 'admin_flag_overrides',
    label: 'Admin feature overrides',
    description: 'Allow this browser session to override the docs admin feature catalog through cookies.',
    defaultEnabled: true,
    scope: 'admin',
  },
];

export function getConfiguredAdminPassword(): string {
  return import.meta.env.DOCS_ADMIN_PASSWORD ?? (import.meta.env.DEV ? DEV_ADMIN_PASSWORD : '');
}

export function getAdminSessionSecret(): string {
  return import.meta.env.DOCS_ADMIN_SESSION_SECRET ?? getConfiguredAdminPassword();
}

export function getPublicPostHogKey(): string {
  return import.meta.env.PUBLIC_POSTHOG_KEY ?? '';
}

export function getPublicPostHogHost(): string {
  return import.meta.env.PUBLIC_POSTHOG_HOST ?? 'https://us.i.posthog.com';
}

export function getPostHogApiKey(): string {
  return import.meta.env.POSTHOG_API_KEY ?? '';
}

export function getPostHogProjectId(): string {
  return import.meta.env.POSTHOG_PROJECT_ID ?? '';
}

export function getPostHogApiHost(): string {
  return import.meta.env.POSTHOG_API_HOST ?? 'https://us.posthog.com';
}

export function isPublicTelemetryConfigured(): boolean {
  return Boolean(getPublicPostHogKey());
}

export function isPostHogQueryConfigured(): boolean {
  return Boolean(getPostHogApiKey() && getPostHogProjectId());
}

export function getAdminConfigSnapshot() {
  const usingDevelopmentPasswordFallback = !import.meta.env.DOCS_ADMIN_PASSWORD && import.meta.env.DEV;
  const explicitSessionSecret = Boolean(import.meta.env.DOCS_ADMIN_SESSION_SECRET);

  return {
    hasAdminPassword: Boolean(getConfiguredAdminPassword()),
    hasExplicitSessionSecret: explicitSessionSecret,
    hasSessionSecret: Boolean(getAdminSessionSecret()),
    posthogQueryConfigured: isPostHogQueryConfigured(),
    publicTelemetryConfigured: isPublicTelemetryConfigured(),
    usingDerivedSessionSecret: !explicitSessionSecret && Boolean(getConfiguredAdminPassword()),
    usingDevelopmentPasswordFallback,
  };
}
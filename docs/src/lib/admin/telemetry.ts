import { getPublicPostHogHost, getPublicPostHogKey } from './config';

type Primitive = boolean | number | string;
type TelemetryContext = Record<string, Primitive | Primitive[] | null | undefined>;

function isSensitiveKey(key: string): boolean {
  return /(password|secret|token|authorization|cookie|key)/i.test(key);
}

function sanitizeValue(value: Primitive | Primitive[] | null | undefined): Primitive | Primitive[] | null {
  if (value === null || value === undefined) return null;
  if (Array.isArray(value)) {
    return value
      .filter((item): item is Primitive => ['boolean', 'number', 'string'].includes(typeof item))
      .map((item) => (typeof item === 'string' ? item.slice(0, 240) : item));
  }

  if (typeof value === 'string') return value.slice(0, 240);
  return value;
}

export function sanitizeTelemetryContext(context: TelemetryContext): Record<string, Primitive | Primitive[] | null> {
  const sanitized: Record<string, Primitive | Primitive[] | null> = {};

  for (const [key, value] of Object.entries(context)) {
    if (isSensitiveKey(key)) continue;
    sanitized[key] = sanitizeValue(value);
  }

  return sanitized;
}

export function logStructured(
  level: 'error' | 'info' | 'warn',
  message: string,
  context: TelemetryContext
): void {
  const payload = {
    context: sanitizeTelemetryContext(context),
    level,
    message,
    timestamp: new Date().toISOString(),
  };

  const writer = level === 'error' ? console.error : level === 'warn' ? console.warn : console.info;
  writer(JSON.stringify(payload));
}

export async function captureServerEvent(
  event: string,
  context: TelemetryContext,
  options?: { distinctId?: string }
): Promise<void> {
  const apiKey = getPublicPostHogKey();
  if (!apiKey) {
    logStructured('info', `Skipped telemetry event ${event}`, {
      reason: 'public_posthog_key_missing',
      ...context,
    });
    return;
  }

  const captureUrl = new URL('/i/v0/e/', getPublicPostHogHost());
  const payload = {
    api_key: apiKey,
    distinct_id: options?.distinctId ?? 'server:anonymous',
    event,
    properties: {
      ...sanitizeTelemetryContext(context),
      '$process_person_profile': false,
      source: 'agents-docs-server',
    },
    timestamp: new Date().toISOString(),
  };

  try {
    const response = await fetch(captureUrl, {
      body: JSON.stringify(payload),
      headers: { 'content-type': 'application/json' },
      method: 'POST',
    });

    if (!response.ok) {
      logStructured('warn', `PostHog capture returned ${response.status}`, {
        event,
        requestId: String(context.request_id ?? ''),
      });
    }
  } catch (error) {
    logStructured('error', 'PostHog capture failed', {
      error: error instanceof Error ? error.message : 'Unknown capture failure',
      event,
      requestId: String(context.request_id ?? ''),
    });
  }
}
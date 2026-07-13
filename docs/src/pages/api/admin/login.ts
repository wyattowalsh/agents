import type { APIRoute } from 'astro';

import { createAdminSession, getAdminDistinctId, getRequesterFingerprint, isAdminPasswordValid, setAdminSessionCookie } from '../../../lib/admin/auth';
import { getAdminSessionSecret } from '../../../lib/admin/config';
import { validateCsrfToken } from '../../../lib/admin/csrf';
import { isTrustedSameOriginRequest, redirectResponse, sanitizeAdminRedirect, withSearchParams } from '../../../lib/admin/http';
import { captureServerEvent, logStructured } from '../../../lib/admin/telemetry';

export const prerender = false;

/** In-process login rate limit (per serverless isolate). Prefer edge WAF in production. */
const LOGIN_WINDOW_MS = 15 * 60 * 1000;
const LOGIN_MAX_FAILURES = 8;
const LOGIN_MAP_MAX_KEYS = 10_000;
const loginFailures = new Map<string, { count: number; firstAt: number }>();

function clientIpForRateLimit(request: Request): string {
  // Prefer operator-configured trusted header, then Vercel, then first XFF hop (spoofable if untrusted).
  const configured = (import.meta.env.DOCS_ADMIN_CLIENT_IP_HEADER as string | undefined)?.trim();
  if (configured) {
    const valued = (request.headers.get(configured) ?? '').split(',')[0]?.trim();
    if (valued) return valued;
  }
  const vercel = (request.headers.get('x-vercel-forwarded-for') ?? '').split(',')[0]?.trim();
  if (vercel) return vercel;
  return (request.headers.get('x-forwarded-for') ?? '').split(',')[0]?.trim() || 'unknown';
}

function rateLimitKey(request: Request, fingerprint: string): string {
  return `${clientIpForRateLimit(request)}|${fingerprint.slice(0, 16)}`;
}

function pruneRateLimitMap(): void {
  if (loginFailures.size <= LOGIN_MAP_MAX_KEYS) return;
  const overflow = loginFailures.size - LOGIN_MAP_MAX_KEYS;
  let removed = 0;
  for (const key of loginFailures.keys()) {
    loginFailures.delete(key);
    removed += 1;
    if (removed >= overflow) break;
  }
}

function isRateLimited(key: string): boolean {
  const now = Date.now();
  const entry = loginFailures.get(key);
  if (!entry) return false;
  if (now - entry.firstAt > LOGIN_WINDOW_MS) {
    loginFailures.delete(key);
    return false;
  }
  return entry.count >= LOGIN_MAX_FAILURES;
}

function recordFailure(key: string): void {
  const now = Date.now();
  const entry = loginFailures.get(key);
  if (!entry || now - entry.firstAt > LOGIN_WINDOW_MS) {
    loginFailures.set(key, { count: 1, firstAt: now });
    pruneRateLimitMap();
    return;
  }
  entry.count += 1;
}

function clearFailures(key: string): void {
  loginFailures.delete(key);
}

export const POST: APIRoute = async ({ cookies, locals, request }) => {
  const requestId = locals.admin.requestId;
  const fingerprint = getRequesterFingerprint(request);
  const limitKey = rateLimitKey(request, fingerprint);

  if (!isTrustedSameOriginRequest(request)) {
    await captureServerEvent(
      'admin_login_failed',
      { outcome: 'origin_rejected', request_id: requestId, route: '/api/admin/login' },
      { distinctId: fingerprint }
    );
    return redirectResponse(request, '/admin/login?error=origin');
  }

  if (isRateLimited(limitKey)) {
    await captureServerEvent(
      'admin_login_failed',
      { outcome: 'rate_limited', request_id: requestId, route: '/api/admin/login' },
      { distinctId: fingerprint }
    );
    return redirectResponse(request, withSearchParams('/admin/login', { error: 'rate_limited' }));
  }

  const formData = await request.formData();
  const csrfToken = String(formData.get('csrf') ?? '');
  const password = String(formData.get('password') ?? '');
  const redirectPath = sanitizeAdminRedirect(formData.get('redirect'));

  if (!validateCsrfToken(cookies, csrfToken)) {
    await captureServerEvent(
      'admin_login_failed',
      { outcome: 'csrf_rejected', request_id: requestId, route: '/api/admin/login' },
      { distinctId: fingerprint }
    );
    return redirectResponse(request, withSearchParams('/admin/login', { error: 'csrf', redirect: redirectPath }));
  }

  if (!password) {
    await captureServerEvent(
      'admin_login_failed',
      { outcome: 'missing_password', request_id: requestId, route: '/api/admin/login' },
      { distinctId: fingerprint }
    );
    return redirectResponse(request, withSearchParams('/admin/login', { error: 'missing_password', redirect: redirectPath }));
  }

  if (!isAdminPasswordValid(password)) {
    // Auth abuse only: wrong password (not CSRF / empty form)
    recordFailure(limitKey);
    await captureServerEvent(
      'admin_login_failed',
      { outcome: 'invalid_password', request_id: requestId, route: '/api/admin/login' },
      { distinctId: fingerprint }
    );
    return redirectResponse(
      request,
      withSearchParams('/admin/login', { error: 'invalid_credentials', redirect: redirectPath })
    );
  }

  // Refuse "successful" login when session crypto is unavailable (non-DEV without secret).
  if (!getAdminSessionSecret()) {
    await captureServerEvent(
      'admin_login_failed',
      { outcome: 'misconfigured', request_id: requestId, route: '/api/admin/login' },
      { distinctId: fingerprint }
    );
    return redirectResponse(
      request,
      withSearchParams('/admin/login', { error: 'misconfigured', redirect: redirectPath })
    );
  }

  clearFailures(limitKey);
  const session = createAdminSession();
  setAdminSessionCookie(cookies, session);

  logStructured('info', 'Admin login accepted', {
    request_id: requestId,
    route: '/api/admin/login',
  });

  await captureServerEvent(
    'admin_login_succeeded',
    { outcome: 'accepted', request_id: requestId, route: redirectPath },
    { distinctId: getAdminDistinctId() }
  );

  return redirectResponse(request, redirectPath);
};
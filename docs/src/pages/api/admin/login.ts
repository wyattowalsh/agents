import type { APIRoute } from 'astro';

import { createAdminSession, getAdminDistinctId, getRequesterFingerprint, isAdminPasswordValid, setAdminSessionCookie } from '../../../lib/admin/auth';
import { validateCsrfToken } from '../../../lib/admin/csrf';
import { isTrustedSameOriginRequest, redirectResponse, sanitizeAdminRedirect, withSearchParams } from '../../../lib/admin/http';
import { captureServerEvent, logStructured } from '../../../lib/admin/telemetry';

export const prerender = false;

export const POST: APIRoute = async ({ cookies, locals, request }) => {
  const requestId = locals.admin.requestId;
  const fingerprint = getRequesterFingerprint(request);

  if (!isTrustedSameOriginRequest(request)) {
    await captureServerEvent(
      'admin_login_failed',
      { outcome: 'origin_rejected', request_id: requestId, route: '/api/admin/login' },
      { distinctId: fingerprint }
    );
    return redirectResponse(request, '/admin/login?error=origin');
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
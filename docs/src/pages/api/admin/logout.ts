import type { APIRoute } from 'astro';

import { clearAdminSessionCookie, getAdminDistinctId } from '../../../lib/admin/auth';
import { validateCsrfToken } from '../../../lib/admin/csrf';
import { isTrustedSameOriginRequest, redirectResponse } from '../../../lib/admin/http';
import { captureServerEvent } from '../../../lib/admin/telemetry';

export const prerender = false;

export const POST: APIRoute = async ({ cookies, locals, request }) => {
  const requestId = locals.admin.requestId;

  if (!isTrustedSameOriginRequest(request)) {
    return new Response(JSON.stringify({ error: 'Origin validation failed', requestId }), {
      headers: { 'content-type': 'application/json' },
      status: 403,
    });
  }

  const formData = await request.formData();
  const csrfToken = String(formData.get('csrf') ?? '');

  if (!validateCsrfToken(cookies, csrfToken)) {
    return new Response(JSON.stringify({ error: 'CSRF validation failed', requestId }), {
      headers: { 'content-type': 'application/json' },
      status: 403,
    });
  }

  clearAdminSessionCookie(cookies);

  await captureServerEvent(
    'admin_logout_succeeded',
    { outcome: 'cleared', request_id: requestId, route: '/api/admin/logout' },
    { distinctId: getAdminDistinctId() }
  );

  return redirectResponse(request, '/admin/login?logged_out=1');
};
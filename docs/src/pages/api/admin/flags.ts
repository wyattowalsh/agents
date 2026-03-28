import type { APIRoute } from 'astro';

import { getAdminDistinctId } from '../../../lib/admin/auth';
import { ADMIN_FEATURE_OVERRIDE_COOKIE } from '../../../lib/admin/config';
import { validateCsrfToken } from '../../../lib/admin/csrf';
import { collectFeatureOverridesFromFormData, serializeFeatureOverrides } from '../../../lib/admin/flags';
import { isTrustedSameOriginRequest, redirectResponse } from '../../../lib/admin/http';
import { captureServerEvent } from '../../../lib/admin/telemetry';

export const prerender = false;

export const POST: APIRoute = async ({ cookies, locals, request }) => {
  const requestId = locals.admin.requestId;

  if (!locals.admin.isAuthenticated) {
    return new Response(JSON.stringify({ error: 'Authentication required', requestId }), {
      headers: { 'content-type': 'application/json' },
      status: 401,
    });
  }

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

  const overrides = collectFeatureOverridesFromFormData(formData);
  const overrideKeys = Object.keys(overrides);

  if (overrideKeys.length) {
    cookies.set(ADMIN_FEATURE_OVERRIDE_COOKIE, serializeFeatureOverrides(overrides), {
      httpOnly: false,
      maxAge: 60 * 60 * 24 * 30,
      path: '/',
      sameSite: 'strict',
      secure: !import.meta.env.DEV,
    });
  } else if (typeof cookies.delete === 'function') {
    cookies.delete(ADMIN_FEATURE_OVERRIDE_COOKIE, { path: '/' });
  } else {
    cookies.set(ADMIN_FEATURE_OVERRIDE_COOKIE, '', {
      httpOnly: false,
      maxAge: 0,
      path: '/',
      sameSite: 'strict',
      secure: !import.meta.env.DEV,
    });
  }

  await captureServerEvent(
    'admin_flag_overrides_saved',
    {
      flags: overrideKeys,
      outcome: 'saved',
      request_id: requestId,
      route: '/api/admin/flags',
    },
    { distinctId: getAdminDistinctId() }
  );

  return redirectResponse(request, '/admin/flags?saved=1');
};
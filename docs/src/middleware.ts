import { randomUUID } from 'node:crypto';

import { defineMiddleware } from 'astro:middleware';

import { readAdminSessionFromCookies } from './lib/admin/auth';
import { ensureCsrfToken } from './lib/admin/csrf';
import { readFeatureOverridesFromCookies } from './lib/admin/flags';

function isProtectedAdminPath(pathname: string): boolean {
  if (pathname.startsWith('/api/admin') && pathname !== '/api/admin/login') return true;
  if (pathname.startsWith('/admin') && pathname !== '/admin/login') return true;
  return false;
}

export const onRequest = defineMiddleware(async (context, next) => {
  const pathname = new URL(context.request.url).pathname;
  const requestId = randomUUID();
  const session = readAdminSessionFromCookies(context.cookies);
  const csrfToken = ensureCsrfToken(context.cookies);
  const featureOverrides = readFeatureOverridesFromCookies(context.cookies);

  context.locals.admin = {
    csrfToken,
    featureOverrides,
    isAuthenticated: Boolean(session),
    requestId,
    session,
  };

  if (pathname === '/admin/login' && session) {
    return context.redirect('/admin');
  }

  if (isProtectedAdminPath(pathname) && !session) {
    if (pathname.startsWith('/api/admin')) {
      return new Response(JSON.stringify({ error: 'Authentication required', requestId }), {
        headers: { 'content-type': 'application/json', 'x-request-id': requestId },
        status: 401,
      });
    }

    const redirectTarget = `/admin/login?redirect=${encodeURIComponent(pathname)}`;
    return context.redirect(redirectTarget);
  }

  const response = await next();
  response.headers.set('x-request-id', requestId);

  if (pathname.startsWith('/admin')) {
    response.headers.set('x-robots-tag', 'noindex, nofollow');
  }

  return response;
});
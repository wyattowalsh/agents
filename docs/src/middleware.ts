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

function isAdminSurfacePath(pathname: string): boolean {
  return pathname.startsWith('/admin') || pathname.startsWith('/api/admin');
}

const SKILL_HUB_SLUGS = new Set(['all', 'install', 'installed', 'catalog']);

function legacySkillCatalogRedirect(pathname: string): string | null {
  const match = pathname.match(/^\/skills\/([^/]+)\/?$/);
  if (!match) return null;
  if (SKILL_HUB_SLUGS.has(match[1])) return null;
  return `/skills/catalog/${match[1]}/`;
}

export const onRequest = defineMiddleware(async (context, next) => {
  const pathname = new URL(context.request.url).pathname;
  const legacyRedirect = legacySkillCatalogRedirect(pathname);
  if (legacyRedirect) {
    return context.redirect(legacyRedirect, 308);
  }
  const requestId = randomUUID();

  if (!isAdminSurfacePath(pathname)) {
    const response = await next();
    response.headers.set('x-request-id', requestId);
    return response;
  }

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

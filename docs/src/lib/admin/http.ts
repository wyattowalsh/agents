export function isTrustedSameOriginRequest(request: Request): boolean {
  const requestOrigin = new URL(request.url).origin;
  const originHeader = request.headers.get('origin');
  const refererHeader = request.headers.get('referer');

  if (originHeader) {
    try {
      return new URL(originHeader).origin === requestOrigin;
    } catch {
      return false;
    }
  }

  if (refererHeader) {
    try {
      return new URL(refererHeader).origin === requestOrigin;
    } catch {
      return false;
    }
  }

  return false;
}

export function sanitizeAdminRedirect(rawValue: FormDataEntryValue | null | undefined): string {
  const candidate = typeof rawValue === 'string' ? rawValue : '/admin';
  if (!candidate.startsWith('/admin')) return '/admin';
  return candidate;
}

export function withSearchParams(
  path: string,
  params: Record<string, number | string | undefined>
): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === '') continue;
    search.set(key, String(value));
  }

  const query = search.toString();
  return query ? `${path}?${query}` : path;
}

export function redirectResponse(request: Request, path: string, status = 303): Response {
  return Response.redirect(new URL(path, request.url), status);
}
import { randomBytes } from 'node:crypto';

import { safeEqualStrings } from './compare';
import { ADMIN_CSRF_COOKIE, ADMIN_CSRF_TTL_SECONDS } from './config';

export function generateCsrfToken(): string {
  return randomBytes(24).toString('base64url');
}

export function ensureCsrfToken(cookies: {
  get: (name: string) => { value: string } | undefined;
  set: (name: string, value: string, options: Record<string, unknown>) => void;
}): string {
  const existing = cookies.get(ADMIN_CSRF_COOKIE)?.value;
  if (existing) return existing;

  const token = generateCsrfToken();
  cookies.set(ADMIN_CSRF_COOKIE, token, {
    httpOnly: false,
    maxAge: ADMIN_CSRF_TTL_SECONDS,
    path: '/',
    sameSite: 'strict',
    secure: !import.meta.env.DEV,
  });
  return token;
}

export function validateCsrfToken(
  cookies: { get: (name: string) => { value: string } | undefined },
  submittedToken: string
): boolean {
  const stored = cookies.get(ADMIN_CSRF_COOKIE)?.value;
  if (!stored || !submittedToken) return false;
  return safeEqualStrings(stored, submittedToken);
}

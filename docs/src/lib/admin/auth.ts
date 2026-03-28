import { createHash, createHmac, randomBytes } from 'node:crypto';

import {
  ADMIN_SESSION_COOKIE,
  ADMIN_SESSION_TTL_SECONDS,
  getAdminSessionSecret,
  getConfiguredAdminPassword,
} from './config';
import { safeEqualStrings } from './compare';

export type AdminSession = {
  actor: 'shared-password';
  expiresAt: number;
  issuedAt: number;
  nonce: string;
};

function hashValue(value: string): Buffer {
  return createHash('sha256').update(value).digest();
}

function signPayload(encodedPayload: string, secret: string): string {
  return createHmac('sha256', secret).update(encodedPayload).digest('base64url');
}

export function isAdminPasswordValid(submittedPassword: string): boolean {
  const configuredPassword = getConfiguredAdminPassword();
  if (!configuredPassword || !submittedPassword) return false;

  return safeEqualStrings(
    hashValue(submittedPassword).toString('base64url'),
    hashValue(configuredPassword).toString('base64url')
  );
}

export function createAdminSession(): AdminSession {
  const issuedAt = Date.now();

  return {
    actor: 'shared-password',
    expiresAt: issuedAt + ADMIN_SESSION_TTL_SECONDS * 1000,
    issuedAt,
    nonce: randomBytes(18).toString('base64url'),
  };
}

export function encodeAdminSession(session: AdminSession): string {
  const secret = getAdminSessionSecret();
  if (!secret) return '';

  const encodedPayload = Buffer.from(JSON.stringify(session), 'utf8').toString('base64url');
  const signature = signPayload(encodedPayload, secret);
  return `${encodedPayload}.${signature}`;
}

export function decodeAdminSession(token: string | undefined): AdminSession | null {
  if (!token) return null;

  const secret = getAdminSessionSecret();
  if (!secret) return null;

  const [encodedPayload, signature] = token.split('.');
  if (!encodedPayload || !signature) return null;

  const expectedSignature = signPayload(encodedPayload, secret);
  if (!safeEqualStrings(signature, expectedSignature)) return null;

  try {
    const parsed = JSON.parse(Buffer.from(encodedPayload, 'base64url').toString('utf8')) as AdminSession;
    if (!parsed?.issuedAt || !parsed?.expiresAt || parsed.actor !== 'shared-password') return null;
    if (parsed.expiresAt <= Date.now()) return null;
    return parsed;
  } catch {
    return null;
  }
}

export function readAdminSessionFromCookies(cookies: {
  get: (name: string) => { value: string } | undefined;
}): AdminSession | null {
  return decodeAdminSession(cookies.get(ADMIN_SESSION_COOKIE)?.value);
}

export function setAdminSessionCookie(cookies: {
  set: (name: string, value: string, options: Record<string, unknown>) => void;
}, session: AdminSession): void {
  const token = encodeAdminSession(session);
  if (!token) return;

  cookies.set(ADMIN_SESSION_COOKIE, token, {
    httpOnly: true,
    maxAge: ADMIN_SESSION_TTL_SECONDS,
    path: '/',
    sameSite: 'strict',
    secure: !import.meta.env.DEV,
  });
}

export function clearAdminSessionCookie(cookies: {
  delete?: (name: string, options?: Record<string, unknown>) => void;
  set: (name: string, value: string, options: Record<string, unknown>) => void;
}): void {
  if (typeof cookies.delete === 'function') {
    cookies.delete(ADMIN_SESSION_COOKIE, { path: '/' });
    return;
  }

  cookies.set(ADMIN_SESSION_COOKIE, '', {
    httpOnly: true,
    maxAge: 0,
    path: '/',
    sameSite: 'strict',
    secure: !import.meta.env.DEV,
  });
}

export function getRequesterFingerprint(request: Request): string {
  const forwardedFor = request.headers.get('x-forwarded-for') ?? 'unknown';
  const userAgent = request.headers.get('user-agent') ?? 'unknown';
  const digest = createHash('sha256').update(`${forwardedFor}|${userAgent}`).digest('hex');
  return `anon:${digest.slice(0, 18)}`;
}

export function getAdminDistinctId(): string {
  return 'admin:shared-password';
}

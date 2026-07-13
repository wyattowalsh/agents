/**
 * Gate: admin redirect allowlist (RV-S-007).
 * Asserts docs/src/lib/admin/http.ts exports isAllowedAdminRedirectPath with the locked predicate,
 * then runs a matrix using that same allow rule.
 */
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const httpTs = resolve(here, '../src/lib/admin/http.ts');
const source = readFileSync(httpTs, 'utf8');

if (!source.includes('export function isAllowedAdminRedirectPath')) {
  console.error('FAIL: isAllowedAdminRedirectPath export missing in http.ts');
  process.exit(1);
}

const predicate = "pathname === '/admin' || pathname.startsWith('/admin/')";
if (!source.includes(predicate)) {
  console.error('FAIL: locked allow predicate missing in http.ts:', predicate);
  process.exit(1);
}

function isAllowedAdminRedirectPath(pathname) {
  return pathname === '/admin' || pathname.startsWith('/admin/');
}

function sanitizeAdminRedirect(raw, baseUrl = 'http://localhost') {
  const candidate = typeof raw === 'string' ? raw : '/admin';
  let normalized;
  try {
    normalized = new URL(candidate, baseUrl).pathname;
  } catch {
    return '/admin';
  }
  if (!isAllowedAdminRedirectPath(normalized)) return '/admin';
  return normalized;
}

const pathMatrix = [
  ['/admin', true],
  ['/admin/', true],
  ['/admin/security', true],
  ['/administrator', false],
  ['/admin-evil', false],
  ['/etc', false],
];

for (const [path, allow] of pathMatrix) {
  const got = isAllowedAdminRedirectPath(path);
  if (got !== allow) {
    console.error('FAIL matrix', path, 'expected', allow, 'got', got);
    process.exit(1);
  }
}

const sanitizeCases = [
  ['/admin', '/admin'],
  ['/admin/flags', '/admin/flags'],
  ['/administrator', '/admin'],
  ['/admin/../etc', '/admin'], // collapses to /etc → denied → /admin
];

for (const [input, expected] of sanitizeCases) {
  const got = sanitizeAdminRedirect(input);
  if (got !== expected) {
    console.error('FAIL sanitize', input, 'expected', expected, 'got', got);
    process.exit(1);
  }
}

console.log('REDIRECT_CHECK_OK');

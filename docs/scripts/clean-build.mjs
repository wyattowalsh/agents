import { rm } from 'node:fs/promises';
import { dirname, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const defaultRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const docsRoot = resolve(process.env.DOCS_CLEAN_BUILD_ROOT || defaultRoot);
const targets = ['dist', '.astro', '.vercel/output'];

for (const target of targets) {
  const path = resolve(docsRoot, target);
  if (path !== docsRoot && path.startsWith(`${docsRoot}${sep}`)) {
    await rm(path, { recursive: true, force: true });
  }
}

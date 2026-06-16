import { SKILL_HUB_SLUGS } from './skillHubSlugs';

export function skillIdForInstallFooter(path: string): string | null {
  const catalogMatch = path.match(/^skills\/catalog\/([^/]+)$/);
  if (catalogMatch) {
    return catalogMatch[1];
  }

  if (!path.startsWith('skills/') || path.startsWith('skills/installed')) {
    return null;
  }

  const remainder = path.slice('skills/'.length);
  if (!remainder || remainder.includes('/') || SKILL_HUB_SLUGS.has(remainder)) {
    return null;
  }

  return remainder;
}

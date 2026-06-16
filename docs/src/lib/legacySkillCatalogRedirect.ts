import { SKILL_HUB_SLUGS } from './skillHubSlugs';

export { SKILL_HUB_SLUGS };

export function legacySkillCatalogRedirect(pathname: string): string | null {
  const match = pathname.match(/^\/skills\/([^/]+)\/?$/);
  if (!match) return null;
  if (SKILL_HUB_SLUGS.has(match[1])) return null;
  return `/skills/catalog/${match[1]}/`;
}

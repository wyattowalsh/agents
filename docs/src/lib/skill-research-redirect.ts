import skillsCatalogIndex from '../../public/generated-registries/skills-catalog-index.json';

/** Keep behavior aligned with wagents/skill_research_redirect.py */

export type SkillCatalogGroup = 'custom' | 'external';

type CatalogSkillRow = {
  name: string;
  sourceKind?: string;
};

type SkillsCatalogIndex = {
  allSkillIndex?: CatalogSkillRow[];
};

const catalogGroups = buildSkillResearchRedirectMap(skillsCatalogIndex as SkillsCatalogIndex);

export function buildSkillResearchRedirectMap(index: SkillsCatalogIndex): Map<string, SkillCatalogGroup> {
  const map = new Map<string, SkillCatalogGroup>();
  for (const entry of index.allSkillIndex ?? []) {
    if (!entry.name) continue;
    map.set(entry.name, entry.sourceKind === 'custom' ? 'custom' : 'external');
  }
  return map;
}

export function parseSkillResearchPath(pathname: string): string | null {
  const match = pathname.match(/^\/skill-research\/([^/]+)\/?$/);
  if (!match) return null;
  return decodeURIComponent(match[1]);
}

export function skillResearchRedirectTarget(skillId: string): string {
  const group = catalogGroups.get(skillId) ?? 'external';
  return `/skills/catalog/${group}/${skillId}/`;
}
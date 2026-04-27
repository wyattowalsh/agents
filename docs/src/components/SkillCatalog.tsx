import { ExternalLink, Search } from 'lucide-react';
import * as React from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';

type Knowledge = {
  headings?: string[];
  references?: string[];
  scripts?: string[];
  templates?: string[];
  evals?: string[];
  data?: string[];
  resourceLinks?: string[];
  wordCount?: number;
};

type SkillRow = {
  name: string;
  title: string;
  description: string;
  sourceType: 'custom' | 'installed' | 'curated-external';
  sourceRoot: string;
  trustTier: string;
  sourceUrl?: string;
  installCommand?: string;
  useCommand: string;
  userInvocable?: boolean;
  status?: string;
  knowledge?: Knowledge;
};

const sourceLabels = {
  all: 'All sources',
  custom: 'Custom',
  installed: 'Installed',
  'curated-external': 'Curated external',
};

function sourceVariant(sourceType: SkillRow['sourceType']) {
  if (sourceType === 'custom') return 'skill';
  if (sourceType === 'installed') return 'installed';
  return 'external';
}

export default function SkillCatalog({ skills }: { skills: SkillRow[] }) {
  const [query, setQuery] = React.useState('');
  const [source, setSource] = React.useState<keyof typeof sourceLabels>('all');
  const [trust, setTrust] = React.useState('all');

  const trustTiers = React.useMemo(
    () => Array.from(new Set(skills.map((skill) => skill.trustTier).filter(Boolean))).sort(),
    [skills]
  );

  const filtered = React.useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return skills.filter((skill) => {
      const matchesSource = source === 'all' || skill.sourceType === source;
      const matchesTrust = trust === 'all' || skill.trustTier === trust;
      const haystack = [
        skill.name,
        skill.description,
        skill.sourceRoot,
        skill.trustTier,
        ...(skill.knowledge?.headings ?? []),
        ...(skill.knowledge?.references ?? []),
      ]
        .join(' ')
        .toLowerCase();
      return matchesSource && matchesTrust && (!normalized || haystack.includes(normalized));
    });
  }, [query, skills, source, trust]);

  return (
    <section className="my-8 grid gap-4">
      <div className="grid gap-3 rounded-lg border border-border bg-[color:var(--surface-panel)] p-4 md:grid-cols-[minmax(0,1fr)_12rem_12rem]">
        <label className="relative block">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            className="pl-9"
            placeholder="Search skills, sources, references..."
            aria-label="Search skills"
          />
        </label>
        <Select value={source} onChange={(event) => setSource(event.target.value as keyof typeof sourceLabels)}>
          {Object.entries(sourceLabels).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </Select>
        <Select value={trust} onChange={(event) => setTrust(event.target.value)}>
          <option value="all">All trust tiers</option>
          {trustTiers.map((tier) => (
            <option key={tier} value={tier}>
              {tier}
            </option>
          ))}
        </Select>
      </div>

      <p className="m-0 text-sm text-muted-foreground">
        Showing {filtered.length} of {skills.length} indexed skills.
      </p>

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {filtered.map((skill) => (
          <Card key={`${skill.sourceType}:${skill.sourceRoot}:${skill.name}`} className="min-w-0">
            <CardHeader>
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant={sourceVariant(skill.sourceType)}>{skill.sourceType}</Badge>
                <Badge>{skill.trustTier}</Badge>
                {skill.status ? <Badge variant="warning">{skill.status}</Badge> : null}
              </div>
              <CardTitle className="break-words">{skill.name}</CardTitle>
              <CardDescription>{skill.description}</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-3 text-sm">
              <dl className="m-0 grid gap-2">
                <div>
                  <dt className="text-xs uppercase text-muted-foreground">Source</dt>
                  <dd className="m-0 break-words font-mono text-xs">{skill.sourceRoot}</dd>
                </div>
                <div className="flex flex-wrap gap-3">
                  <span>{skill.knowledge?.wordCount ?? 0} words</span>
                  <span>{skill.knowledge?.references?.length ?? 0} refs</span>
                  <span>{skill.knowledge?.scripts?.length ?? 0} scripts</span>
                  <span>{skill.knowledge?.evals?.length ?? 0} evals</span>
                </div>
              </dl>
              <div className="flex flex-wrap gap-2">
                {skill.sourceType === 'custom' ? (
                  <Button asChild size="sm" variant="secondary">
                    <a href={`/skills/${skill.name}/`}>Details</a>
                  </Button>
                ) : null}
                {skill.sourceUrl ? (
                  <Button asChild size="sm" variant="outline">
                    <a href={skill.sourceUrl} target="_blank" rel="noreferrer">
                      <ExternalLink className="h-4 w-4" />
                      Source
                    </a>
                  </Button>
                ) : null}
              </div>
              {skill.installCommand ? (
                <pre className="agents-scrollbar m-0 max-w-full overflow-x-auto rounded-md border border-border p-2 text-xs">
                  <code className="block min-w-max whitespace-pre">{skill.installCommand}</code>
                </pre>
              ) : null}
            </CardContent>
          </Card>
        ))}
      </div>
    </section>
  );
}

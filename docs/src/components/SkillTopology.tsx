import * as d3 from 'd3';
import * as React from 'react';

type SkillRow = {
  name: string;
  sourceType: string;
  trustTier: string;
};

const colorBySource = d3
  .scaleOrdinal<string, string>()
  .domain(['custom', 'installed', 'curated-external'])
  .range(['#a78bfa', '#fbbf24', '#22d3ee']);

export default function SkillTopology({ skills }: { skills: SkillRow[] }) {
  const visible = React.useMemo(() => skills.slice(0, 96), [skills]);
  const nodes = React.useMemo(() => {
    const radius = 148;
    return visible.map((skill, index) => {
      const angle = (index / Math.max(visible.length, 1)) * Math.PI * 2 - Math.PI / 2;
      return {
        ...skill,
        x: 190 + Math.cos(angle) * radius,
        y: 190 + Math.sin(angle) * radius,
        r: skill.sourceType === 'custom' ? 5.5 : 4.5,
      };
    });
  }, [visible]);

  if (!skills.length) return null;

  return (
    <figure className="my-8 overflow-hidden rounded-lg border border-border bg-[color:var(--surface-panel)]">
      <svg viewBox="0 0 380 380" role="img" aria-label="Skill source topology" className="block h-auto w-full">
        <defs>
          <radialGradient id="skill-topology-core">
            <stop offset="0%" stopColor="currentColor" stopOpacity="0.55" />
            <stop offset="100%" stopColor="currentColor" stopOpacity="0" />
          </radialGradient>
        </defs>
        <circle cx="190" cy="190" r="72" fill="url(#skill-topology-core)" className="text-primary" />
        <circle cx="190" cy="190" r="38" fill="none" stroke="currentColor" strokeOpacity="0.25" />
        {nodes.map((node) => (
          <line
            key={`edge:${node.sourceType}:${node.name}`}
            x1="190"
            y1="190"
            x2={node.x}
            y2={node.y}
            stroke={colorBySource(node.sourceType)}
            strokeOpacity="0.18"
          />
        ))}
        {nodes.map((node) => (
          <g key={`${node.sourceType}:${node.name}`}>
            <circle cx={node.x} cy={node.y} r={node.r} fill={colorBySource(node.sourceType)} opacity="0.88" />
            <title>
              {node.name} · {node.sourceType} · {node.trustTier}
            </title>
          </g>
        ))}
        <text x="190" y="184" textAnchor="middle" className="fill-current font-mono text-[14px] font-semibold">
          skills
        </text>
        <text x="190" y="204" textAnchor="middle" className="fill-current font-mono text-[10px]" opacity="0.68">
          {skills.length} indexed
        </text>
      </svg>
      <figcaption className="grid gap-2 border-t border-border p-4 text-sm text-muted-foreground">
        <strong className="text-foreground">Source topology</strong>
        <span>Generated from the same custom, installed, and curated external skill index used by the catalog.</span>
      </figcaption>
    </figure>
  );
}

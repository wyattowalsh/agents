interface FilterBarProps {
  query: string;
  onQueryChange: (q: string) => void;
  activeTier: string;
  onTierChange: (tier: string) => void;
}

const TIERS = ["all", "strong", "moderate", "weak"];

export function FilterBar({ query, onQueryChange, activeTier, onTierChange }: FilterBarProps) {
  return (
    <div className="filter-bar">
      <input
        type="search"
        placeholder="Search opportunities..."
        value={query}
        onChange={(e) => onQueryChange(e.target.value)}
        aria-label="Search opportunities"
      />
      <div className="tier-pills">
        {TIERS.map((t) => (
          <button
            key={t}
            className={activeTier === t ? "active" : ""}
            onClick={() => onTierChange(t)}
          >
            {t === "all" ? "All" : t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>
    </div>
  );
}

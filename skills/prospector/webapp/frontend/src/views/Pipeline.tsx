import { useState, useMemo } from "react";
import { fetchOpportunities } from "../api";
import { useApi } from "../hooks/useApi";
import { FilterBar } from "../components/FilterBar";
import { OpportunityCard } from "../components/OpportunityCard";
import { Loading } from "../components/Loading";
import { PIPELINE_ORDER, STATUS_LABELS } from "../types";

export function Pipeline() {
  const { data: opps, loading, error } = useApi(() => fetchOpportunities({ limit: 500 }));
  const [query, setQuery] = useState("");
  const [tierFilter, setTierFilter] = useState("all");

  const filtered = useMemo(() => {
    if (!opps) return [];
    const q = query.toLowerCase();
    return opps.filter((o) => {
      if (tierFilter !== "all" && o.triage_tier !== tierFilter) return false;
      if (q && !`${o.title} ${o.one_liner} ${o.niche}`.toLowerCase().includes(q)) return false;
      return true;
    });
  }, [opps, query, tierFilter]);

  const columns = useMemo(() => {
    const map: Record<string, typeof filtered> = {};
    for (const s of PIPELINE_ORDER) map[s] = [];
    for (const o of filtered) {
      if (map[o.status]) map[o.status].push(o);
    }
    return PIPELINE_ORDER.filter((s) => (map[s]?.length ?? 0) > 0).map((s) => ({
      status: s,
      opps: map[s],
    }));
  }, [filtered]);

  if (loading) return <Loading />;
  if (error) return <div className="err"><h2>Error</h2><p>{error}</p></div>;
  if (!opps?.length) return <div className="glass empty">No opportunities yet. Run /prospector to start scanning.</div>;

  return (
    <>
      <FilterBar query={query} onQueryChange={setQuery} activeTier={tierFilter} onTierChange={setTierFilter} />
      <div className="kanban">
        {columns.map(({ status, opps: col }) => (
          <div key={status} className="kanban-col">
            <h3>
              {STATUS_LABELS[status] || status}
              <span className="count">({col.length})</span>
            </h3>
            {col.map((o) => (
              <OpportunityCard key={o.id} opp={o} />
            ))}
          </div>
        ))}
      </div>
    </>
  );
}

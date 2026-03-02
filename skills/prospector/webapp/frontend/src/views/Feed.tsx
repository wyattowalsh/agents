import { useState, useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { fetchOpportunities } from "../api";
import { useApi } from "../hooks/useApi";
import { FilterBar } from "../components/FilterBar";
import { OpportunityCard } from "../components/OpportunityCard";
import { Loading } from "../components/Loading";

export function Feed() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const sessionFilter = searchParams.get("session") ?? undefined;
  const { data: opps, loading, error } = useApi(
    () => fetchOpportunities({ sort: "created_at", sort_dir: "desc", limit: 500, session_id: sessionFilter }),
    [sessionFilter],
  );
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

  if (loading) return <Loading />;
  if (error) return <div className="err"><h2>Error</h2><p>{error}</p></div>;
  if (!opps?.length) return <div className="glass empty">No opportunities yet.</div>;

  return (
    <>
      {sessionFilter && (
        <div className="session-banner glass">
          <span>Session: <span className="mono" style={{ fontSize: "0.75rem" }}>{sessionFilter}</span></span>
          <button onClick={() => navigate("/feed")} style={{ fontSize: "0.72rem" }}>
            Clear filter
          </button>
        </div>
      )}
      <FilterBar query={query} onQueryChange={setQuery} activeTier={tierFilter} onTierChange={setTierFilter} />
      <div className="feed">
        {filtered.map((o) => (
          <OpportunityCard key={o.id} opp={o} showDate />
        ))}
      </div>
    </>
  );
}

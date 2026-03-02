import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchOpportunities } from "../api";
import { useApi } from "../hooks/useApi";
import { TierBadge, StatusBadge } from "../components/Badge";
import { FilterBar } from "../components/FilterBar";
import { Loading } from "../components/Loading";
import { SIGNAL_LABELS } from "../types";

const TIER_ORDER: Record<string, number> = { strong: 0, moderate: 1, weak: 2 };

export function Leaderboard() {
  const { data: opps, loading, error } = useApi(() => fetchOpportunities({ limit: 500 }));
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [tierFilter, setTierFilter] = useState("all");

  const ranked = useMemo(() => {
    if (!opps) return [];
    const q = query.toLowerCase();
    const filtered = opps.filter((o) => {
      if (tierFilter !== "all" && o.triage_tier !== tierFilter) return false;
      if (q && !`${o.title} ${o.one_liner} ${o.niche}`.toLowerCase().includes(q)) return false;
      return true;
    });
    return [...filtered].sort((a, b) => {
      const ta = TIER_ORDER[a.triage_tier || ""] ?? 3;
      const tb = TIER_ORDER[b.triage_tier || ""] ?? 3;
      if (ta !== tb) return ta - tb;
      return (b.evidence?.length || 0) - (a.evidence?.length || 0);
    });
  }, [opps, query, tierFilter]);

  if (loading) return <Loading />;
  if (error) return <div className="err"><h2>Error</h2><p>{error}</p></div>;
  if (!opps?.length) return <div className="glass empty">No opportunities yet.</div>;

  return (
    <div className="leaderboard">
      <FilterBar query={query} onQueryChange={setQuery} activeTier={tierFilter} onTierChange={setTierFilter} />
      <table className="lb-table">
        <thead>
          <tr>
            <th>#</th>
            <th>ID</th>
            <th>Title</th>
            <th>Tier</th>
            <th>Status</th>
            <th>Signal</th>
            <th>Evidence</th>
            <th>Niche</th>
          </tr>
        </thead>
        <tbody>
          {ranked.map((o, i) => (
            <tr key={o.id} onClick={() => navigate(`/detail/${o.id}`)}>
              <td className="lb-rank">{i + 1}</td>
              <td className="mono" style={{ fontSize: "0.75rem", color: "var(--muted)" }}>
                {o.id}
              </td>
              <td>{o.title}</td>
              <td><TierBadge tier={o.triage_tier} /></td>
              <td><StatusBadge status={o.status} /></td>
              <td style={{ fontSize: "0.78rem" }}>
                {SIGNAL_LABELS[o.primary_signal] || o.primary_signal}
              </td>
              <td style={{ textAlign: "center" }}>{o.evidence?.length || 0}</td>
              <td className="pill" style={{ margin: 0 }}>{o.niche}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

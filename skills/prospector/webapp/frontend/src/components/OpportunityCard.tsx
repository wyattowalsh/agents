import { useNavigate } from "react-router-dom";
import type { Opportunity } from "../types";
import { SIGNAL_LABELS } from "../types";
import { TierBadge, StatusBadge } from "./Badge";
import { TriageMini } from "./TriageGrid";

interface Props {
  opp: Opportunity;
  showDate?: boolean;
}

export function OpportunityCard({ opp, showDate }: Props) {
  const navigate = useNavigate();

  return (
    <div className="glass opp-card" onClick={() => navigate(`/detail/${opp.id}`)}>
      <div className="opp-title">
        <span className="opp-id mono">{opp.id}</span>
        <span>{opp.title}</span>
      </div>
      <div className="opp-liner">{opp.one_liner}</div>
      <div className="opp-meta">
        <TierBadge tier={opp.triage_tier} />
        <StatusBadge status={opp.status} />
        <span className="pill">{opp.niche}</span>
        <span className="pill">{SIGNAL_LABELS[opp.primary_signal] || opp.primary_signal}</span>
        {opp.mvp_days && <span className="pill">{opp.mvp_days}d MVP</span>}
        {opp.mvp_tech_stack && <span className="pill">{opp.mvp_tech_stack}</span>}
      </div>
      <TriageMini opp={opp} />
      {showDate && opp.created_at && (
        <div className="opp-date">{opp.created_at.slice(0, 10)}</div>
      )}
    </div>
  );
}

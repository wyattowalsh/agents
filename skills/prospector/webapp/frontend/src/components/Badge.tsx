import { STATUS_LABELS } from "../types";

export function TierBadge({ tier }: { tier?: string }) {
  if (!tier) return <span className="badge">?</span>;
  return <span className={`badge tier-${tier.toLowerCase()}`}>{tier}</span>;
}

export function StatusBadge({ status }: { status: string }) {
  return <span className="badge status-badge">{STATUS_LABELS[status] || status}</span>;
}

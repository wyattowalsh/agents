import type { Evidence } from "../types";
import { SIGNAL_LABELS } from "../types";

export function EvidenceSection({ evidence }: { evidence: Evidence[] }) {
  if (!evidence.length) return null;
  return (
    <div className="detail-section">
      <h3>Evidence ({evidence.length})</h3>
      <div className="ev-list">
        {evidence.map((ev, i) => (
          <div key={ev.id ?? i} className="ev-item">
            {ev.quote && <div className="ev-quote">"{ev.quote}"</div>}
            <div className="ev-meta">
              {ev.source_category && <span>{ev.source_category}</span>}
              {ev.signal_type && <span>{SIGNAL_LABELS[ev.signal_type] || ev.signal_type}</span>}
              {ev.intensity && <span>{ev.intensity}</span>}
              {ev.source_tool && <span>{ev.source_tool}</span>}
              {ev.source_url && (
                <a href={ev.source_url} target="_blank" rel="noopener noreferrer">
                  {ev.source_url}
                </a>
              )}
              {ev.payment_signal ? (
                <span style={{ color: "var(--ok)", fontWeight: 700 }}>$</span>
              ) : null}
            </div>
            {ev.context && <div className="fs td mt-s">{ev.context}</div>}
          </div>
        ))}
      </div>
    </div>
  );
}

export function CounterEvidence({ json }: { json?: string }) {
  if (!json) return null;
  let items: (string | { claim?: string; source?: string; impact?: string })[];
  try {
    items = JSON.parse(json);
  } catch {
    return null;
  }
  if (!items.length) return null;
  return (
    <div className="detail-section">
      <h3 style={{ color: "var(--bad)" }}>Why This Might Be Wrong</h3>
      <div className="counter-list">
        {items.map((ce, i) => {
          const text = typeof ce === "string" ? ce : ce.claim ?? JSON.stringify(ce);
          const impact = typeof ce === "object" && ce.impact ? ce.impact : null;
          return (
            <div key={i} className="counter-item">
              {text}
              {impact && (
                <span className="pill" style={{ marginLeft: "0.4rem", fontSize: "0.68rem" }}>
                  {impact} impact
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

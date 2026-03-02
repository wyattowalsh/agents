import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { fetchOpportunity, updateOpportunity, deleteOpportunity } from "../api";
import { useApi } from "../hooks/useApi";
import { useToast } from "../components/Toast";
import { TierBadge, StatusBadge } from "../components/Badge";
import { TriageFull } from "../components/TriageGrid";
import { EvidenceSection, CounterEvidence } from "../components/EvidenceList";
import { Loading } from "../components/Loading";
import { VALID_TRANSITIONS, SIGNAL_LABELS } from "../types";

export function Detail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const { data: opp, loading, error, refetch } = useApi(() => fetchOpportunity(id!), [id]);
  const [notes, setNotes] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") navigate(-1);
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [navigate]);

  if (loading) return <Loading />;
  if (error) return <div className="err"><h2>Error</h2><p>{error}</p></div>;
  if (!opp) return <div className="glass empty">Opportunity not found.</div>;

  const transitions = VALID_TRANSITIONS[opp.status] || [];
  const currentNotes = notes ?? opp.notes ?? "";

  const handleTransition = async (newStatus: string) => {
    try {
      setSaving(true);
      await updateOpportunity(opp.id, { status: newStatus });
      toast(`Status changed to ${newStatus}`, "success");
      refetch();
    } catch (e) {
      toast(e instanceof Error ? e.message : "Update failed", "error");
    } finally {
      setSaving(false);
    }
  };

  const handleSaveNotes = async () => {
    try {
      setSaving(true);
      await updateOpportunity(opp.id, { notes: currentNotes });
      toast("Notes saved", "success");
      setNotes(null);
      refetch();
    } catch (e) {
      toast(e instanceof Error ? e.message : "Save failed", "error");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    try {
      await deleteOpportunity(opp.id);
      toast(`Deleted ${opp.id}`, "success");
      navigate("/pipeline");
    } catch (e) {
      toast(e instanceof Error ? e.message : "Delete failed", "error");
    }
  };

  // Parse panel JSON if present
  let panel: { final_verdict?: string; synthesis?: string; conditions?: string[] } | null = null;
  if (opp.panel_json) {
    try {
      panel = typeof opp.panel_json === "string" ? JSON.parse(opp.panel_json) : opp.panel_json;
    } catch {
      /* ignore */
    }
  }

  return (
    <div className="detail">
      <div className="detail-header glass">
        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", marginBottom: "0.3rem" }}>
          <button onClick={() => navigate(-1)} style={{ fontSize: "0.78rem" }}>
            &larr; Back
          </button>
          {!confirmDelete ? (
            <button
              onClick={() => setConfirmDelete(true)}
              style={{ fontSize: "0.78rem", color: "var(--bad)", borderColor: "var(--bad)" }}
            >
              Delete
            </button>
          ) : (
            <span style={{ display: "flex", gap: "0.3rem", alignItems: "center" }}>
              <span style={{ fontSize: "0.78rem", color: "var(--bad)" }}>
                Delete {opp.id}?
              </span>
              <button
                onClick={handleDelete}
                disabled={saving}
                style={{
                  fontSize: "0.78rem",
                  background: "var(--bad)",
                  color: "oklch(0.15 0.02 260)",
                  borderColor: "var(--bad)",
                }}
              >
                Yes
              </button>
              <button onClick={() => setConfirmDelete(false)} style={{ fontSize: "0.78rem" }}>
                Cancel
              </button>
            </span>
          )}
          <span style={{ fontSize: "0.65rem", color: "var(--muted)", marginLeft: "auto" }}>
            ESC ← back
          </span>
        </div>
        <h2>
          <span className="mono" style={{ color: "var(--muted)", marginRight: "0.4rem" }}>
            {opp.id}
          </span>
          {opp.title}
        </h2>
        <div className="detail-meta">
          <TierBadge tier={opp.triage_tier} />
          <StatusBadge status={opp.status} />
          <span className="pill">{opp.niche}</span>
          <span className="pill">{SIGNAL_LABELS[opp.primary_signal] || opp.primary_signal}</span>
          {opp.mvp_days && <span className="pill">{opp.mvp_days}d MVP</span>}
          {opp.mvp_tech_stack && <span className="pill">{opp.mvp_tech_stack}</span>}
          {opp.created_at && (
            <span style={{ fontSize: "0.72rem", color: "var(--muted)" }}>
              {opp.created_at.slice(0, 10)}
            </span>
          )}
        </div>
        {opp.one_liner && <p className="td mt-s">{opp.one_liner}</p>}

        {transitions.length > 0 && (
          <div className="status-actions">
            {transitions.map((s) => (
              <button key={s} disabled={saving} onClick={() => handleTransition(s)}>
                &rarr; {s}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="detail-section glass mt-m">
        <h3>Triage</h3>
        <TriageFull opp={opp} />
        {opp.triage_reasoning && <p className="fs td mt-s">{opp.triage_reasoning}</p>}
      </div>

      {opp.evidence?.length > 0 && (
        <div className="glass mt-m">
          <EvidenceSection evidence={opp.evidence} />
        </div>
      )}

      <div className="glass mt-m">
        <CounterEvidence json={opp.counter_evidence_json} />
      </div>

      {panel && panel.final_verdict && (
        <div className="detail-section glass mt-m">
          <h3>Expert Panel</h3>
          <div style={{ marginBottom: "0.4rem" }}>
            <span
              className="badge"
              style={{
                background:
                  panel.final_verdict === "go"
                    ? "var(--ok)"
                    : panel.final_verdict === "nogo"
                      ? "var(--bad)"
                      : "var(--warn)",
                color: "oklch(0.15 0.02 260)",
              }}
            >
              Panel: {panel.final_verdict}
            </span>
          </div>
          {panel.synthesis && <p className="fs td">{panel.synthesis}</p>}
          {panel.conditions && panel.conditions.length > 0 && (
            <ul style={{ marginTop: "0.3rem", paddingLeft: "1.2rem", listStyle: "disc" }}>
              {panel.conditions.map((c, i) => (
                <li key={i} className="fs td">
                  {c}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      <div className="detail-section glass mt-m">
        <h3>Notes</h3>
        <textarea
          className="notes-area"
          value={currentNotes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Add notes..."
        />
        <div className="status-actions">
          <button disabled={saving || notes === null} onClick={handleSaveNotes}>
            Save notes
          </button>
        </div>
      </div>
    </div>
  );
}

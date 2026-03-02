import { useNavigate } from "react-router-dom";
import { fetchSessions } from "../api";
import { useApi } from "../hooks/useApi";
import { Loading } from "../components/Loading";

export function Sessions() {
  const navigate = useNavigate();
  const { data: sessions, loading, error } = useApi(() => fetchSessions());

  if (loading) return <Loading />;
  if (error) return <div className="err"><h2>Error</h2><p>{error}</p></div>;
  if (!sessions?.length) return <div className="glass empty">No sessions recorded yet.</div>;

  return (
    <div className="sessions-wrap">
      <table className="sessions-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Mode</th>
            <th>Seed</th>
            <th>Opportunities</th>
            <th>Waves</th>
            <th>Status</th>
            <th>Started</th>
            <th>Completed</th>
          </tr>
        </thead>
        <tbody>
          {sessions.map((s) => (
            <tr
              key={s.id}
              onClick={() => navigate(`/feed?session=${s.id}`)}
              title="View opportunities from this session"
              style={{ cursor: "pointer" }}
            >
              <td className="mono" style={{ fontSize: "0.75rem" }}>
                {s.id}
              </td>
              <td>{s.mode}</td>
              <td>{s.seed_query || "-"}</td>
              <td style={{ textAlign: "center" }}>{s.opportunities_found}</td>
              <td style={{ textAlign: "center" }}>{s.wave_completed}</td>
              <td>
                <span
                  className="badge"
                  style={{
                    background:
                      s.status === "complete"
                        ? "var(--ok)"
                        : s.status === "interrupted"
                          ? "var(--warn)"
                          : "var(--info)",
                    color: "oklch(0.15 0.02 260)",
                  }}
                >
                  {s.status}
                </span>
              </td>
              <td style={{ fontSize: "0.78rem" }}>{s.started_at?.slice(0, 16).replace("T", " ") || "-"}</td>
              <td style={{ fontSize: "0.78rem" }}>{s.completed_at?.slice(0, 16).replace("T", " ") || "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

import { fetchStats, exportUrl } from "../api";
import { useApi } from "../hooks/useApi";
import { Loading } from "../components/Loading";

const TIER_COLORS: Record<string, string> = {
  strong: "var(--ok)",
  moderate: "var(--warn)",
  weak: "var(--bad)",
};

function BarChart({
  title,
  data,
  colorFn,
  total = 0,
}: {
  title: string;
  data: Record<string, number>;
  colorFn?: (key: string) => string;
  total?: number;
}) {
  const entries = Object.entries(data).sort(([, a], [, b]) => b - a);
  const max = Math.max(...entries.map(([, v]) => v), 1);

  return (
    <div className="glass stat-card">
      <h3>{title}</h3>
      {entries.map(([key, count]) => (
        <div key={key} className="stat-bar-row">
          <span className="sbl">{key}</span>
          <div className="stat-bar-track">
            <div
              className="stat-bar-fill"
              style={{
                width: `${(count / max) * 100}%`,
                background: colorFn ? colorFn(key) : "var(--accent)",
              }}
            />
          </div>
          <span className="sbn">
              {count}
              {total > 0 && (
                <span style={{ fontSize: "0.65rem", color: "var(--muted)", marginLeft: "0.25em" }}>
                  {Math.round((count / total) * 100)}%
                </span>
              )}
            </span>
        </div>
      ))}
      {entries.length === 0 && <p className="td fs">No data</p>}
    </div>
  );
}

export function Stats() {
  const { data: stats, loading, error } = useApi(() => fetchStats());

  if (loading) return <Loading />;
  if (error) return <div className="err"><h2>Error</h2><p>{error}</p></div>;
  if (!stats) return null;

  return (
    <div className="stats-grid">
      <div className="glass stat-card" style={{ textAlign: "center" }}>
        <h3>Total Opportunities</h3>
        <div style={{ fontSize: "2.5rem", fontWeight: 700, color: "var(--accent)" }}>
          {stats.total}
        </div>
      </div>
      <BarChart
        title="By Tier"
        data={stats.by_tier}
        colorFn={(k) => TIER_COLORS[k] || "var(--accent)"}
        total={stats.total}
      />
      <BarChart title="By Status" data={stats.by_status} total={stats.total} />
      <BarChart title="By Signal" data={stats.by_signal} />
      <BarChart title="By Niche" data={stats.by_niche} />
      <div className="glass stat-card">
        <h3>Export</h3>
        <div className="export-links">
          <a href={exportUrl("json")} download className="export-btn">
            JSON
          </a>
          <a href={exportUrl("csv")} download className="export-btn">
            CSV
          </a>
          <a href={exportUrl("html")} download className="export-btn">
            HTML Report
          </a>
        </div>
      </div>
    </div>
  );
}

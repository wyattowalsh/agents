import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useApi } from "../hooks/useApi";
import { fetchStats } from "../api";
import { useEffect } from "react";

export function Layout() {
  const { data: stats } = useApi(() => fetchStats());

  const location = useLocation();

  useEffect(() => {
    const titleMap: Record<string, string> = {
      "/pipeline": "Pipeline",
      "/feed": "Feed",
      "/leaderboard": "Leaderboard",
      "/stats": "Stats",
      "/profile": "Profile",
      "/sessions": "Sessions",
      "/detail": "Detail",
    };
    const label =
      Object.entries(titleMap).find(([k]) => location.pathname.startsWith(k))?.[1] ??
      "Prospector";
    document.title = `${label} — Prospector`;
  }, [location.pathname]);

  return (
    <>
      <header className="topbar">
        <h1>Prospector</h1>
        {stats && (
          <div className="topbar-stats">
            <div className="stat">
              <span className="stat-n">{stats.total}</span> total
            </div>
            {stats.by_tier.strong != null && (
              <div className="stat">
                <span className="stat-n" style={{ color: "var(--ok)" }}>
                  {stats.by_tier.strong || 0}
                </span>{" "}
                strong
              </div>
            )}
          </div>
        )}
        <nav className="nav-links">
          <NavLink to="/pipeline">Pipeline</NavLink>
          <NavLink to="/feed">Feed</NavLink>
          <NavLink to="/leaderboard">Leaderboard</NavLink>
          <NavLink to="/stats">Stats</NavLink>
          <NavLink to="/profile">Profile</NavLink>
          <NavLink to="/sessions">Sessions</NavLink>
        </nav>
      </header>
      <main className="main-wrap">
        <Outlet />
      </main>
    </>
  );
}

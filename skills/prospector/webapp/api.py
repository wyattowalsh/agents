"""FastAPI application for the prospector dashboard."""

from __future__ import annotations

import contextlib
import csv
import datetime
import io
import json
import re
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .db import ALL_STATUSES, VALID_TRANSITIONS, get_conn, row_to_dict
from .models import OpportunityUpdate, ProfileData


def create_app(db_path: str) -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="Prospector Dashboard", version="0.2.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8765", "http://localhost:5173", "http://127.0.0.1:8765"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def _conn():
        return get_conn(db_path)

    def _fetch_opps_with_evidence(where: str = "", where_params: list | None = None) -> list[dict]:
        con = _conn()
        try:
            sql = f"SELECT * FROM opportunities {where} ORDER BY created_at DESC"
            rows = con.execute(sql, where_params or []).fetchall()
            results = [row_to_dict(r) for r in rows]
            if results:
                opp_ids = [r["id"] for r in results]
                ph = ",".join("?" * len(opp_ids))
                ev_rows = con.execute(
                    f"SELECT * FROM evidence WHERE opportunity_id IN ({ph}) ORDER BY opportunity_id, id",
                    opp_ids,
                ).fetchall()
                ev_by: dict[str, list] = {r["id"]: [] for r in results}
                for e in ev_rows:
                    d = row_to_dict(e)
                    ev_by.get(d["opportunity_id"], []).append(d)
                for r in results:
                    r["evidence"] = ev_by.get(r["id"], [])
            return results
        finally:
            con.close()

    # ------------------------------------------------------------------
    # Opportunities
    # ------------------------------------------------------------------

    @app.get("/api/opportunities")
    def list_opportunities(
        status: str | None = Query(None),
        tier: str | None = Query(None),
        niche: str | None = Query(None),
        q: str | None = Query(None, max_length=200, description="Text search on title and one_liner"),
        sort: str = Query("created_at"),
        sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
        limit: int = Query(50, ge=1, le=500),
        offset: int = Query(0, ge=0),
        session_id: str | None = Query(None),
    ) -> list[dict]:
        clauses: list[str] = []
        params: list = []

        if status:
            clauses.append("status = ?")
            params.append(status)
        if tier:
            clauses.append("triage_tier = ?")
            params.append(tier)
        if niche:
            clauses.append("niche LIKE ?")
            params.append(f"%{niche}%")
        if session_id:
            clauses.append("session_id = ?")
            params.append(session_id)
        if q:
            clauses.append("(title LIKE ? OR one_liner LIKE ?)")
            params.extend([f"%{q}%", f"%{q}%"])

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        allowed_sorts = {"created_at", "updated_at", "title", "triage_tier", "status", "niche"}
        sort_col = sort if sort in allowed_sorts else "created_at"
        direction = "ASC" if sort_dir.lower() == "asc" else "DESC"

        sql = f"SELECT * FROM opportunities {where} ORDER BY {sort_col} {direction} LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        con = _conn()
        try:
            rows = con.execute(sql, params).fetchall()
            results = [row_to_dict(r) for r in rows]
            if results:
                opp_ids = [r["id"] for r in results]
                placeholders = ",".join("?" * len(opp_ids))
                ev_rows = con.execute(
                    f"SELECT * FROM evidence WHERE opportunity_id IN ({placeholders}) ORDER BY opportunity_id, id",
                    opp_ids,
                ).fetchall()
                ev_by_opp: dict[str, list] = {r["id"]: [] for r in results}
                for e in ev_rows:
                    ev_dict = row_to_dict(e)
                    oid = ev_dict["opportunity_id"]
                    if oid in ev_by_opp:
                        ev_by_opp[oid].append(ev_dict)
                for r in results:
                    r["evidence"] = ev_by_opp.get(r["id"], [])
            return results
        finally:
            con.close()

    @app.get("/api/opportunities/{opp_id}")
    def get_opportunity(opp_id: str) -> dict:
        con = _conn()
        try:
            row = con.execute("SELECT * FROM opportunities WHERE id = ?", (opp_id,)).fetchone()
            if not row:
                raise HTTPException(404, f"Opportunity {opp_id} not found")
            d = row_to_dict(row)
            ev = con.execute(
                "SELECT * FROM evidence WHERE opportunity_id = ? ORDER BY id",
                (opp_id,),
            ).fetchall()
            d["evidence"] = [row_to_dict(e) for e in ev]
            return d
        finally:
            con.close()

    @app.patch("/api/opportunities/{opp_id}")
    async def update_opportunity(opp_id: str, body: OpportunityUpdate) -> dict:
        con = _conn()
        try:
            row = con.execute("SELECT * FROM opportunities WHERE id = ?", (opp_id,)).fetchone()
            if not row:
                raise HTTPException(404, f"Opportunity {opp_id} not found")

            current = row_to_dict(row)
            new_status = body.status

            if new_status:
                if new_status not in ALL_STATUSES:
                    raise HTTPException(400, f"Invalid status: {new_status}")
                allowed = VALID_TRANSITIONS.get(current["status"], set())
                if new_status not in allowed:
                    raise HTTPException(
                        400,
                        f"Cannot transition from '{current['status']}' to '{new_status}'. "
                        f"Allowed: {sorted(allowed) if allowed else 'none (terminal state)'}",
                    )

            updates: list[str] = []
            params: list[str] = []

            if new_status:
                updates.append("status = ?")
                params.append(new_status)
            if body.notes is not None:
                updates.append("notes = ?")
                params.append(body.notes)

            if not updates:
                raise HTTPException(400, "No valid fields to update")

            updates.append("updated_at = strftime('%Y-%m-%dT%H:%M:%S','now')")
            params.append(opp_id)

            con.execute(f"UPDATE opportunities SET {', '.join(updates)} WHERE id = ?", params)
            con.commit()
            return get_opportunity(opp_id)
        finally:
            con.close()

    @app.delete("/api/opportunities/{opp_id}")
    def delete_opportunity(opp_id: str) -> dict:
        con = _conn()
        try:
            row = con.execute("SELECT id FROM opportunities WHERE id = ?", (opp_id,)).fetchone()
            if not row:
                raise HTTPException(404, f"Opportunity {opp_id} not found")
            con.execute("DELETE FROM opportunities WHERE id = ?", (opp_id,))
            con.commit()
            return {"deleted": opp_id}
        finally:
            con.close()

    # ------------------------------------------------------------------
    # Sessions
    # ------------------------------------------------------------------

    @app.get("/api/sessions")
    def list_sessions() -> list[dict]:
        con = _conn()
        try:
            rows = con.execute("SELECT * FROM sessions ORDER BY started_at DESC").fetchall()
            return [row_to_dict(r) for r in rows]
        finally:
            con.close()

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    @app.get("/api/stats")
    def get_stats() -> dict:
        con = _conn()
        try:
            status_rows = con.execute(
                "SELECT status, COUNT(*) as count FROM opportunities GROUP BY status"
            ).fetchall()
            tier_rows = con.execute(
                "SELECT triage_tier, COUNT(*) as count FROM opportunities GROUP BY triage_tier"
            ).fetchall()
            signal_rows = con.execute(
                "SELECT primary_signal, COUNT(*) as count FROM opportunities GROUP BY primary_signal"
            ).fetchall()
            niche_rows = con.execute(
                "SELECT niche, COUNT(*) as count FROM opportunities GROUP BY niche ORDER BY count DESC"
            ).fetchall()
            total = con.execute("SELECT COUNT(*) as count FROM opportunities").fetchone()

            return {
                "total": total["count"] if total else 0,
                "by_status": {r["status"]: r["count"] for r in status_rows},
                "by_tier": {r["triage_tier"]: r["count"] for r in tier_rows if r["triage_tier"]},
                "by_signal": {r["primary_signal"]: r["count"] for r in signal_rows},
                "by_niche": {r["niche"]: r["count"] for r in niche_rows},
            }
        finally:
            con.close()

    # ------------------------------------------------------------------
    # Profile
    # ------------------------------------------------------------------

    @app.get("/api/profile")
    def get_profile() -> dict:
        con = _conn()
        try:
            row = con.execute("SELECT * FROM builder_profile WHERE id = 1").fetchone()
            if not row:
                return {}
            d = row_to_dict(row)
            for key in ("tech_stack", "constraints", "interests", "avoid"):
                if isinstance(d.get(key), str):
                    with contextlib.suppress(json.JSONDecodeError, TypeError):
                        d[key] = json.loads(d[key])
            return d
        finally:
            con.close()

    @app.put("/api/profile")
    async def update_profile(body: ProfileData) -> dict:
        con = _conn()
        try:
            existing = con.execute("SELECT id FROM builder_profile WHERE id = 1").fetchone()

            fields: dict[str, str | int | None] = {}
            if body.tech_stack is not None:
                fields["tech_stack"] = json.dumps(body.tech_stack)
            if body.constraints is not None:
                fields["constraints"] = json.dumps(body.constraints)
            if body.time_budget_hours_week is not None:
                fields["time_budget_hours_week"] = body.time_budget_hours_week
            if body.revenue_goal_mrr is not None:
                fields["revenue_goal_mrr"] = body.revenue_goal_mrr
            if body.interests is not None:
                fields["interests"] = json.dumps(body.interests)
            if body.avoid is not None:
                fields["avoid"] = json.dumps(body.avoid)

            if existing:
                if fields:
                    sets = ", ".join(f"{k} = ?" for k in fields)
                    sets += ", updated_at = strftime('%Y-%m-%dT%H:%M:%S','now')"
                    con.execute(f"UPDATE builder_profile SET {sets} WHERE id = 1", list(fields.values()))
            else:
                cols = ["id"] + list(fields.keys())
                vals = ["1"] + ["?" for _ in fields]
                con.execute(
                    f"INSERT INTO builder_profile ({', '.join(cols)}) VALUES ({', '.join(vals)})",
                    list(fields.values()),
                )

            con.commit()
            return get_profile()
        finally:
            con.close()

    # ------------------------------------------------------------------
    # Export — specific route before parameterized route
    # ------------------------------------------------------------------

    @app.get("/api/export/html")
    def export_html() -> StreamingResponse:
        template_path = Path(__file__).parent.parent / "templates" / "dashboard.html"
        if not template_path.exists():
            raise HTTPException(404, "dashboard.html template not found")

        con = _conn()
        try:
            rows = con.execute("SELECT * FROM opportunities ORDER BY triage_tier, created_at DESC").fetchall()
            opps = []
            if rows:
                all_ids = [r["id"] for r in rows]
                placeholders = ",".join("?" * len(all_ids))
                ev_rows = con.execute(
                    f"SELECT * FROM evidence WHERE opportunity_id IN ({placeholders}) ORDER BY opportunity_id, id",
                    all_ids,
                ).fetchall()
                ev_by_opp: dict[str, list] = {r["id"]: [] for r in rows}
                for e in ev_rows:
                    ev_dict = row_to_dict(e)
                    oid = ev_dict["opportunity_id"]
                    if oid in ev_by_opp:
                        ev_by_opp[oid].append(ev_dict)
                for r in rows:
                    d = row_to_dict(r)
                    d["evidence"] = ev_by_opp.get(d["id"], [])
                    d["counter_evidence"] = []
                    with contextlib.suppress(json.JSONDecodeError, TypeError):
                        d["counter_evidence"] = json.loads(d.get("counter_evidence_json") or "[]")
                    opps.append(d)
        finally:
            con.close()

        payload = {
            "metadata": {
                "date": datetime.date.today().isoformat(),
                "total_opportunities": len(opps),
                "session_mode": "export",
            },
            "opportunities": opps,
        }
        data_json = json.dumps(payload, indent=2, default=str)

        template_html = template_path.read_text(encoding="utf-8")
        updated = re.sub(
            r'(<script\s+id="data"\s+type="application/json">)[\s\S]*?(</script>)',
            lambda m: f"{m.group(1)}\n{data_json}\n{m.group(2)}",
            template_html,
            count=1,
        )

        return StreamingResponse(
            iter([updated]),
            media_type="text/html",
            headers={"Content-Disposition": "attachment; filename=prospector-report.html"},
        )

    @app.get("/api/export/{fmt}", response_model=None)
    def export_data(fmt: str) -> StreamingResponse | JSONResponse:
        if fmt not in ("json", "csv"):
            raise HTTPException(400, "Format must be 'json' or 'csv'")

        opps = _fetch_opps_with_evidence()

        if fmt == "json":
            return JSONResponse(opps)

        buf = io.StringIO()
        if opps:
            csv_cols = [
                "id", "title", "one_liner", "niche", "status", "primary_signal",
                "triage_tier", "triage_bootstrappability", "triage_pmf",
                "triage_competition", "triage_revenue", "triage_technical",
                "triage_moat", "mvp_days", "mvp_tech_stack",
                "created_at", "updated_at", "notes",
            ]
            writer = csv.DictWriter(buf, fieldnames=csv_cols, extrasaction="ignore")
            writer.writeheader()
            for opp in opps:
                writer.writerow(opp)

        return StreamingResponse(
            iter([buf.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=prospector-export.csv"},
        )

    # ------------------------------------------------------------------
    # Static frontend — mount LAST so API routes take priority
    # ------------------------------------------------------------------

    dist_dir = Path(__file__).parent / "frontend" / "dist"
    if dist_dir.exists():
        app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="frontend")

    return app

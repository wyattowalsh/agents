"""Prospector Dashboard — FastAPI server for opportunity pipeline management."""

from __future__ import annotations

import argparse
import contextlib
import csv
import datetime
import io
import json
import re
import sqlite3
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

# ---------------------------------------------------------------------------
# Lifecycle transition rules
# ---------------------------------------------------------------------------
_VALID_TRANSITIONS: dict[str, set[str]] = {
    "discovered": {"evaluated", "parked", "rejected"},
    "evaluated": {"researching", "parked", "rejected"},
    "researching": {"building", "parked"},
    "building": {"launched", "parked"},
    "launched": {"parked"},
    "parked": set(),
    "rejected": set(),
}

_ALL_STATUSES = set(_VALID_TRANSITIONS.keys())

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = FastAPI(title="Prospector Dashboard", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_db_path: str = ""


def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(_db_path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    return con


def _row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/api/opportunities")
def list_opportunities(
    status: str | None = Query(None),
    tier: str | None = Query(None),
    niche: str | None = Query(None),
    q: str | None = Query(None, description="Text search on title and one_liner"),
    sort: str = Query("created_at"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
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

    if q:
        clauses.append("(title LIKE ? OR one_liner LIKE ?)")
        params.extend([f"%{q}%", f"%{q}%"])

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    allowed_sorts = {
        "created_at", "updated_at", "title", "triage_tier", "status", "niche",
    }
    sort_col = sort if sort in allowed_sorts else "created_at"

    direction = "ASC" if sort_dir.lower() == "asc" else "DESC"
    sql = f"SELECT * FROM opportunities {where} ORDER BY {sort_col} {direction} LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    con = _conn()
    try:
        rows = con.execute(sql, params).fetchall()
        results = [_row_to_dict(r) for r in rows]
        if results:
            opp_ids = [r["id"] for r in results]
            placeholders = ",".join("?" * len(opp_ids))
            ev_rows = con.execute(
                f"SELECT * FROM evidence WHERE opportunity_id IN ({placeholders}) ORDER BY opportunity_id, id",
                opp_ids,
            ).fetchall()
            ev_by_opp: dict[str, list] = {r["id"]: [] for r in results}
            for e in ev_rows:
                ev_dict = _row_to_dict(e)
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
        d = _row_to_dict(row)
        ev = con.execute(
            "SELECT * FROM evidence WHERE opportunity_id = ? ORDER BY id",
            (opp_id,),
        ).fetchall()
        d["evidence"] = [_row_to_dict(e) for e in ev]
        return d
    finally:
        con.close()


@app.patch("/api/opportunities/{opp_id}")
async def update_opportunity(opp_id: str, request: Request) -> dict:
    body = await request.json()
    con = _conn()
    try:
        row = con.execute("SELECT * FROM opportunities WHERE id = ?", (opp_id,)).fetchone()
        if not row:
            raise HTTPException(404, f"Opportunity {opp_id} not found")

        current = _row_to_dict(row)

        new_status = body.get("status")
        if new_status:
            if new_status not in _ALL_STATUSES:
                raise HTTPException(400, f"Invalid status: {new_status}")
            allowed = _VALID_TRANSITIONS.get(current["status"], set())
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
        if "notes" in body:
            updates.append("notes = ?")
            params.append(body["notes"])

        if not updates:
            raise HTTPException(400, "No valid fields to update")

        updates.append("updated_at = strftime('%Y-%m-%dT%H:%M:%S','now')")
        params.append(opp_id)

        con.execute(
            f"UPDATE opportunities SET {', '.join(updates)} WHERE id = ?",
            params,
        )
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


@app.get("/api/sessions")
def list_sessions() -> list[dict]:
    con = _conn()
    try:
        rows = con.execute("SELECT * FROM sessions ORDER BY started_at DESC").fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        con.close()


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


@app.get("/api/profile")
def get_profile() -> dict:
    con = _conn()
    try:
        row = con.execute("SELECT * FROM builder_profile WHERE id = 1").fetchone()
        if not row:
            return {}
        d = _row_to_dict(row)
        for key in ("tech_stack", "constraints", "interests", "avoid"):
            if isinstance(d.get(key), str):
                with contextlib.suppress(json.JSONDecodeError, TypeError):
                    d[key] = json.loads(d[key])
        return d
    finally:
        con.close()


@app.put("/api/profile")
async def update_profile(request: Request) -> dict:
    body = await request.json()
    con = _conn()
    try:
        existing = con.execute("SELECT id FROM builder_profile WHERE id = 1").fetchone()

        fields = {
            "tech_stack": json.dumps(body["tech_stack"]) if "tech_stack" in body else None,
            "constraints": json.dumps(body["constraints"]) if "constraints" in body else None,
            "time_budget_hours_week": body.get("time_budget_hours_week"),
            "revenue_goal_mrr": body.get("revenue_goal_mrr"),
            "interests": json.dumps(body["interests"]) if "interests" in body else None,
            "avoid": json.dumps(body["avoid"]) if "avoid" in body else None,
        }
        fields = {k: v for k, v in fields.items() if v is not None}

        if existing:
            if fields:
                sets = ", ".join(f"{k} = ?" for k in fields)
                sets += ", updated_at = strftime('%Y-%m-%dT%H:%M:%S','now')"
                con.execute(
                    f"UPDATE builder_profile SET {sets} WHERE id = 1",
                    list(fields.values()),
                )
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


@app.get("/api/export/{fmt}")
def export_data(fmt: str) -> StreamingResponse | list[dict]:
    if fmt not in ("json", "csv"):
        raise HTTPException(400, "Format must be 'json' or 'csv'")

    con = _conn()
    try:
        rows = con.execute("SELECT * FROM opportunities ORDER BY created_at DESC").fetchall()
        opps = []
        for r in rows:
            d = _row_to_dict(r)
            ev = con.execute(
                "SELECT * FROM evidence WHERE opportunity_id = ? ORDER BY id",
                (d["id"],),
            ).fetchall()
            d["evidence"] = [_row_to_dict(e) for e in ev]
            opps.append(d)

        if fmt == "json":
            return JSONResponse(opps)

        # CSV export — flat columns
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
    finally:
        con.close()


@app.get("/api/export/html")
def export_html() -> StreamingResponse:
    """Export all opportunities as a self-contained HTML report using the static template."""
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
                ev_dict = _row_to_dict(e)
                oid = ev_dict["opportunity_id"]
                if oid in ev_by_opp:
                    ev_by_opp[oid].append(ev_dict)
            for r in rows:
                d = _row_to_dict(r)
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
    # Replace the placeholder JSON in the data script tag
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


@app.get("/")
def serve_index() -> FileResponse:
    html = Path(__file__).parent / "index.html"
    if not html.exists():
        raise HTTPException(404, "index.html not found")
    return FileResponse(html, media_type="text/html")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prospector Dashboard Server")
    parser.add_argument("--port", type=int, default=8765, help="Port (default: 8765)")
    parser.add_argument(
        "--db",
        type=str,
        default=str(Path.home() / ".claude" / "prospector" / "prospector.db"),
        help="Path to SQLite database",
    )
    args = parser.parse_args()
    _db_path = args.db
    uvicorn.run(app, host="0.0.0.0", port=args.port)

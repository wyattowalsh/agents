"""Pydantic models for the prospector API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    id: int | None = None
    opportunity_id: str | None = None
    source_category: str = ""
    signal_type: str = ""
    source_url: str | None = None
    source_tool: str | None = None
    quote: str | None = None
    intensity: str | None = None
    payment_signal: int = 0
    context: str | None = None
    accessed_at: str | None = None


class Opportunity(BaseModel):
    id: str
    title: str
    one_liner: str
    niche: str
    status: str = "discovered"
    primary_signal: str
    triage_bootstrappability: str | None = None
    triage_pmf: str | None = None
    triage_competition: str | None = None
    triage_revenue: str | None = None
    triage_technical: str | None = None
    triage_moat: str | None = None
    triage_tier: str | None = None
    triage_reasoning: str | None = None
    counter_evidence_json: str | None = None
    panel_json: str | None = None
    panel_verdict: str | None = None
    mvp_days: int | None = None
    mvp_tech_stack: str | None = None
    session_id: str = ""
    seed_query: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    notes: str | None = None
    evidence: list[Evidence] = Field(default_factory=list)


class OpportunityUpdate(BaseModel):
    status: str | None = None
    notes: str | None = None


class ProfileData(BaseModel):
    tech_stack: list[str] | None = None
    constraints: list[str] | None = None
    time_budget_hours_week: int | None = None
    revenue_goal_mrr: int | None = None
    interests: list[str] | None = None
    avoid: list[str] | None = None


class Stats(BaseModel):
    total: int = 0
    by_status: dict[str, int] = Field(default_factory=dict)
    by_tier: dict[str, int] = Field(default_factory=dict)
    by_signal: dict[str, int] = Field(default_factory=dict)
    by_niche: dict[str, int] = Field(default_factory=dict)


class Session(BaseModel):
    id: str
    mode: str
    seed_query: str | None = None
    source_filter: str | None = None
    opportunities_found: int = 0
    wave_completed: int = 0
    status: str = "in_progress"
    started_at: str | None = None
    completed_at: str | None = None

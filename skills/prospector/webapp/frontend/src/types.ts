export interface Evidence {
  id?: number;
  opportunity_id?: string;
  source_category: string;
  signal_type: string;
  source_url?: string;
  source_tool?: string;
  quote?: string;
  intensity?: string;
  payment_signal: number;
  context?: string;
  accessed_at?: string;
}

export interface Opportunity {
  id: string;
  title: string;
  one_liner: string;
  niche: string;
  status: string;
  primary_signal: string;
  triage_bootstrappability?: string;
  triage_pmf?: string;
  triage_competition?: string;
  triage_revenue?: string;
  triage_technical?: string;
  triage_moat?: string;
  triage_tier?: string;
  triage_reasoning?: string;
  counter_evidence_json?: string;
  panel_json?: string;
  panel_verdict?: string;
  mvp_days?: number;
  mvp_tech_stack?: string;
  session_id: string;
  seed_query?: string;
  created_at?: string;
  updated_at?: string;
  notes?: string;
  evidence: Evidence[];
}

export interface Stats {
  total: number;
  by_status: Record<string, number>;
  by_tier: Record<string, number>;
  by_signal: Record<string, number>;
  by_niche: Record<string, number>;
}

export interface Session {
  id: string;
  mode: string;
  seed_query?: string;
  source_filter?: string;
  opportunities_found: number;
  wave_completed: number;
  status: string;
  started_at?: string;
  completed_at?: string;
}

export interface Profile {
  tech_stack?: string[];
  constraints?: string[];
  time_budget_hours_week?: number;
  revenue_goal_mrr?: number;
  interests?: string[];
  avoid?: string[];
  updated_at?: string;
}

export const VALID_TRANSITIONS: Record<string, string[]> = {
  discovered: ["evaluated", "parked", "rejected"],
  evaluated: ["researching", "parked", "rejected"],
  researching: ["building", "parked"],
  building: ["launched", "parked"],
  launched: ["parked"],
  parked: [],
  rejected: [],
};

export const SIGNAL_LABELS: Record<string, string> = {
  pain_no_solution: "Pain + No Solution",
  dying_product: "Dying Product",
  platform_expansion: "Platform Expansion",
  rising_trend: "Rising Trend",
  terrible_ux: "Terrible UX",
  manual_workflow: "Manual Workflow",
};

export const STATUS_LABELS: Record<string, string> = {
  discovered: "Discovered",
  evaluated: "Evaluated",
  researching: "Researching",
  building: "Building",
  launched: "Launched",
  parked: "Parked",
  rejected: "Rejected",
};

export const DIMENSION_LABELS: Record<string, string> = {
  triage_bootstrappability: "Bootstrap",
  triage_pmf: "PMF",
  triage_competition: "Competition",
  triage_revenue: "Revenue",
  triage_technical: "Technical",
  triage_moat: "Moat",
};

export const TRIAGE_DIMENSIONS = [
  "triage_bootstrappability",
  "triage_pmf",
  "triage_competition",
  "triage_revenue",
  "triage_technical",
  "triage_moat",
] as const;

export const PIPELINE_ORDER = [
  "discovered",
  "evaluated",
  "researching",
  "building",
  "launched",
  "parked",
  "rejected",
];

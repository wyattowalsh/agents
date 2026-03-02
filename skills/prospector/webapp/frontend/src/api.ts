import type { Opportunity, Stats, Session, Profile } from "./types";

const BASE = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json();
}

export interface ListParams {
  status?: string;
  tier?: string;
  niche?: string;
  q?: string;
  sort?: string;
  sort_dir?: string;
  limit?: number;
  offset?: number;
  session_id?: string;
}

export async function fetchOpportunities(params?: ListParams): Promise<Opportunity[]> {
  const sp = new URLSearchParams();
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null && v !== "") sp.set(k, String(v));
    }
  }
  const qs = sp.toString();
  return request<Opportunity[]>(`/opportunities${qs ? `?${qs}` : ""}`);
}

export async function fetchOpportunity(id: string): Promise<Opportunity> {
  return request<Opportunity>(`/opportunities/${encodeURIComponent(id)}`);
}

export async function updateOpportunity(
  id: string,
  body: { status?: string; notes?: string },
): Promise<Opportunity> {
  return request<Opportunity>(`/opportunities/${encodeURIComponent(id)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function deleteOpportunity(id: string): Promise<{ deleted: string }> {
  return request<{ deleted: string }>(`/opportunities/${encodeURIComponent(id)}`, {
    method: "DELETE",
  });
}

export async function fetchStats(): Promise<Stats> {
  return request<Stats>("/stats");
}

export async function fetchSessions(): Promise<Session[]> {
  return request<Session[]>("/sessions");
}

export async function fetchProfile(): Promise<Profile> {
  return request<Profile>("/profile");
}

export async function updateProfile(body: Partial<Profile>): Promise<Profile> {
  return request<Profile>("/profile", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function exportUrl(fmt: "json" | "csv" | "html"): string {
  return `${BASE}/export/${fmt}`;
}

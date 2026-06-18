// Feasibility Study API client + report types.
// Kept in its own module so it does not collide with the existing lib/api.ts.

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ---- types ---------------------------------------------------------------

export interface FeasibilityInput {
  session_id: string;
  concept: string;
  location_address: string;
  user_id?: string;
  business_profile_id?: string;
  scale_seats?: number;
  startup_budget?: number;
}

export type FeasibilityStatus = "pending" | "running" | "completed" | "failed";

export interface FeasibilityProgress {
  step: number;
  steps_total: number;
  label: string;
}

export interface Verdict {
  decision: "GO" | "GO_WITH_CONDITIONS" | "NO_GO";
  score: number;
  rationale: string;
  confidence: string;
}

export interface ExecSummary {
  summary_paragraphs: string[];
  key_findings: string[];
  recommendation?: { verdict?: string; rationale?: string };
}

export interface SourceRef {
  section: string;
  label: string;
  detail: string;
  confidence: string;
}

// Widget payloads are rendered defensively; fields mirror the backend
// widget_extractor / service outputs. Most are optional.
export interface FeasibilityReport {
  meta: {
    generated_at: string;
    title: string;
    concept: string;
    business_type: string;
    location: { address: string; lat: number; lng: number; place_id?: string };
    naics_code: string;
    scale_seats?: number | null;
    startup_budget?: number | null;
    schema_version: number;
  };
  verdict: Verdict;
  exec_summary: ExecSummary;
  sections: {
    location?: Record<string, unknown> | null;
    market_size?: Record<string, unknown> | null;
    competition?: {
      competitors?: Record<string, unknown> | null;
      positioning?: Record<string, unknown> | null;
      swot?: Record<string, unknown> | null;
      five_forces?: Record<string, unknown> | null;
      pricing?: Record<string, unknown> | null;
      market_share?: Record<string, unknown> | null;
    };
    consumer?: {
      sentiment?: Record<string, unknown> | null;
      pain_points?: Record<string, unknown> | null;
      profile?: Record<string, unknown> | null;
      data_available?: boolean;
      reviews_analyzed?: number;
    };
    economic?: {
      snapshot?: Record<string, unknown> | null;
      seasonality?: Record<string, unknown> | null;
      entry_timing?: Record<string, unknown> | null;
    };
    financial?: Record<string, unknown> | null;
    fnb_signals?: {
      health_inspections?: Record<string, unknown>;
      walkability?: Record<string, unknown>;
      search_trends?: Record<string, unknown>;
      popular_times?: Record<string, unknown>;
    };
    recommendations?: Array<Record<string, unknown>>;
  };
  sources: SourceRef[];
}

export interface FeasibilityRow {
  id: string;
  session_id: string;
  concept: string;
  location_address: string;
  status: FeasibilityStatus;
  progress?: FeasibilityProgress | null;
  error?: string | null;
  verdict?: string | null;
  viability_score?: number | null;
  title?: string | null;
  report?: FeasibilityReport | null;
  created_at?: string;
  completed_at?: string | null;
}

export interface FeasibilitySummary {
  id: string;
  concept: string;
  location_address: string;
  status: FeasibilityStatus;
  verdict?: string | null;
  viability_score?: number | null;
  title?: string | null;
  created_at?: string;
}

// ---- client --------------------------------------------------------------

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json();
}

export async function createFeasibilityReport(input: FeasibilityInput): Promise<FeasibilityRow> {
  const res = await fetch(`${API_URL}/api/feasibility/reports`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  const data = await json<{ report: FeasibilityRow }>(res);
  return data.report;
}

export async function fetchFeasibilityReport(id: string): Promise<FeasibilityRow> {
  const res = await fetch(`${API_URL}/api/feasibility/reports/${id}`);
  const data = await json<{ report: FeasibilityRow }>(res);
  return data.report;
}

export async function listFeasibilityReports(
  sessionId: string,
  userId?: string
): Promise<FeasibilitySummary[]> {
  const params = new URLSearchParams();
  if (userId) params.set("user_id", userId);
  else params.set("session_id", sessionId);
  const res = await fetch(`${API_URL}/api/feasibility/reports?${params}`);
  const data = await json<{ reports: FeasibilitySummary[] }>(res);
  return data.reports;
}

export async function rerunFeasibilityReport(id: string): Promise<void> {
  await fetch(`${API_URL}/api/feasibility/reports/${id}/rerun`, { method: "POST" });
}

export async function deleteFeasibilityReport(id: string): Promise<void> {
  await fetch(`${API_URL}/api/feasibility/reports/${id}`, { method: "DELETE" });
}

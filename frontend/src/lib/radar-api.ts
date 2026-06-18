// Business Radar API client + types. Separate module to avoid colliding with lib/api.ts.

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type RadarSeverity = "info" | "watch" | "urgent";
export type RadarCategory =
  | "competition"
  | "regulation"
  | "supply"
  | "demand"
  | "macro"
  | "local"
  | "reputation";

export interface RadarAlert {
  id: string;
  title: string;
  url?: string | null;
  source?: string | null;
  source_domain?: string | null;
  published_at?: string | null;
  category: RadarCategory;
  severity: RadarSeverity;
  relevance_score: number;
  summary?: string | null;
  why_it_matters?: string | null;
  suggested_action?: string | null;
  status: "new" | "read" | "dismissed";
  created_at: string;
}

export interface RadarSubscription {
  id: string;
  business_profile_id: string;
  name?: string | null;
  watch_topics: string[];
  categories: string[];
  frequency: string;
  schedule_hour: number;
  status: string;
  last_scanned_at?: string | null;
}

export interface RadarScan {
  id: string;
  status: string;
  candidates_found?: number;
  alerts_created?: number;
  started_at?: string;
  completed_at?: string | null;
}

export interface RadarFeed {
  subscription: RadarSubscription | null;
  alerts: RadarAlert[];
  unread_count: number;
  latest_scan: RadarScan | null;
}

export interface RadarSubscriptionUpdate {
  business_profile_id: string;
  watch_topics?: string[];
  categories?: string[];
  frequency?: string;
  schedule_hour?: number;
  status?: string;
}

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail || detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json();
}

export async function fetchRadarFeed(
  businessProfileId: string,
  status?: string,
  limit = 50
): Promise<RadarFeed> {
  const params = new URLSearchParams({ business_profile_id: businessProfileId, limit: String(limit) });
  if (status) params.set("status", status);
  return json<RadarFeed>(await fetch(`${API_URL}/api/radar/feed?${params}`));
}

export async function getOrCreateRadarSubscription(
  businessProfileId: string
): Promise<RadarSubscription> {
  const res = await fetch(`${API_URL}/api/radar/subscription?business_profile_id=${businessProfileId}`);
  return (await json<{ subscription: RadarSubscription }>(res)).subscription;
}

export async function updateRadarSubscription(
  payload: RadarSubscriptionUpdate
): Promise<RadarSubscription> {
  const res = await fetch(`${API_URL}/api/radar/subscription`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return (await json<{ subscription: RadarSubscription }>(res)).subscription;
}

export async function triggerRadarScan(
  businessProfileId: string
): Promise<{ subscription_id: string; status: string }> {
  const res = await fetch(`${API_URL}/api/radar/scan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ business_profile_id: businessProfileId }),
  });
  return json(res);
}

export async function markRadarAlert(alertId: string, action: "read" | "dismiss"): Promise<void> {
  await fetch(`${API_URL}/api/radar/alerts/${alertId}/${action}`, { method: "POST" });
}

// ---- shared UI helpers ----

export function severityStyle(sev: RadarSeverity): { badge: string; dot: string } {
  switch (sev) {
    case "urgent":
      return { badge: "bg-red-500/15 text-red-300 border-red-500/30", dot: "bg-red-400" };
    case "watch":
      return { badge: "bg-amber-500/15 text-amber-300 border-amber-500/30", dot: "bg-amber-400" };
    default:
      return { badge: "bg-blue-500/15 text-blue-300 border-blue-500/30", dot: "bg-blue-400" };
  }
}

export function relativeTime(iso?: string | null): string {
  if (!iso) return "";
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "";
  const diff = Date.now() - then;
  const m = Math.floor(diff / 60000);
  if (m < 1) return "just now";
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

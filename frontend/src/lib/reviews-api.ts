// Reputation Hub API client + types. Separate module (mirrors radar-api.ts).

import * as mock from "./reviews-mock";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Run the Hub UI on in-browser sample data (no backend) when either flag is set.
// NEXT_PUBLIC_API_MOCK=1 turns on mocks app-wide; NEXT_PUBLIC_REVIEWS_MOCK=1 is reviews-only.
export const REVIEWS_MOCK =
  process.env.NEXT_PUBLIC_REVIEWS_MOCK === "1" || process.env.NEXT_PUBLIC_API_MOCK === "1";

export type ResponseStatus = "needs_response" | "drafted" | "responded";
export type Sentiment = "positive" | "neutral" | "mixed" | "negative";
export type InboxFilter = "all" | "unreplied" | "negative";

export interface ReviewConnection {
  id: string;
  business_profile_id: string;
  platform: string;
  location_label?: string | null;
  status: string;
  last_sync_at?: string | null;
  last_sync_status?: string | null;
  last_error?: string | null;
}

export interface Review {
  id: string;
  source: string;
  external_review_id: string;
  author_name?: string | null;
  author_photo_url?: string | null;
  rating?: number | null;
  review_text?: string | null;
  review_created_at?: string | null;
  review_url?: string | null;
  sentiment?: Sentiment | null;
  themes?: string[] | null;
  response_status: ResponseStatus;
  response_text?: string | null;
  response_published_at?: string | null;
}

export interface ReviewDraft {
  tone: string;
  text: string;
}

export interface ReviewAnalytics {
  total_reviews: number;
  average_rating: number | null;
  needs_response: number;
  response_rate: number;
  sentiment: { positive: number; neutral: number; mixed: number; negative: number };
  top_themes: { theme: string; count: number }[];
  rating_trend: { recent_30d: number | null; prior_30d: number | null };
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

export async function fetchConnections(bid: string): Promise<ReviewConnection[]> {
  if (REVIEWS_MOCK) return mock.fetchConnections(bid);
  const res = await fetch(`${API_URL}/api/reviews/connections?business_profile_id=${bid}`);
  return (await json<{ connections: ReviewConnection[] }>(res)).connections;
}

export async function startGoogleConnect(bid: string): Promise<{ authorization_url: string }> {
  if (REVIEWS_MOCK) return mock.startGoogleConnect();
  return json(
    await fetch(`${API_URL}/api/reviews/connect/google/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ business_profile_id: bid }),
    })
  );
}

export async function deleteConnection(id: string): Promise<void> {
  if (REVIEWS_MOCK) return mock.deleteConnection();
  await fetch(`${API_URL}/api/reviews/connections/${id}`, { method: "DELETE" });
}

export async function syncReviews(bid: string): Promise<{ synced: number; status: string }> {
  if (REVIEWS_MOCK) return mock.syncReviews();
  return json(
    await fetch(`${API_URL}/api/reviews/sync`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ business_profile_id: bid }),
    })
  );
}

export async function fetchInbox(
  bid: string,
  filter: InboxFilter = "all",
  source?: string
): Promise<Review[]> {
  if (REVIEWS_MOCK) return mock.fetchInbox(bid, filter, source);
  const params = new URLSearchParams({ business_profile_id: bid, filter });
  if (source) params.set("source", source);
  const res = await fetch(`${API_URL}/api/reviews/inbox?${params}`);
  return (await json<{ reviews: Review[] }>(res)).reviews;
}

export async function generateDrafts(reviewId: string): Promise<ReviewDraft[]> {
  if (REVIEWS_MOCK) return mock.generateDrafts(reviewId);
  const res = await fetch(`${API_URL}/api/reviews/${reviewId}/draft`, { method: "POST" });
  return (await json<{ drafts: ReviewDraft[] }>(res)).drafts;
}

export async function publishReply(reviewId: string, text: string): Promise<Review> {
  if (REVIEWS_MOCK) return mock.publishReply(reviewId, text);
  const res = await fetch(`${API_URL}/api/reviews/${reviewId}/publish`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  return (await json<{ review: Review }>(res)).review;
}

export async function fetchAnalytics(bid: string): Promise<ReviewAnalytics> {
  if (REVIEWS_MOCK) return mock.fetchAnalytics();
  return json(await fetch(`${API_URL}/api/reviews/analytics/summary?business_profile_id=${bid}`));
}

export async function addManualReview(payload: {
  business_profile_id: string;
  review_text: string;
  author_name?: string;
  rating?: number;
}): Promise<Review> {
  if (REVIEWS_MOCK) return mock.addManualReview(payload);
  const res = await fetch(`${API_URL}/api/reviews/manual`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return (await json<{ review: Review }>(res)).review;
}

// ---- UI helpers ----

export function sentimentStyle(s?: Sentiment | null): { badge: string; label: string } {
  switch (s) {
    case "positive":
      return { badge: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30", label: "Positive" };
    case "negative":
      return { badge: "bg-red-500/15 text-red-300 border-red-500/30", label: "Negative" };
    case "mixed":
      return { badge: "bg-amber-500/15 text-amber-300 border-amber-500/30", label: "Mixed" };
    default:
      return { badge: "bg-white/10 text-white/60 border-white/15", label: "Neutral" };
  }
}

export function statusStyle(s: ResponseStatus): { badge: string; label: string } {
  switch (s) {
    case "responded":
      return { badge: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30", label: "Responded" };
    case "drafted":
      return { badge: "bg-blue-500/15 text-blue-300 border-blue-500/30", label: "Drafted" };
    default:
      return { badge: "bg-amber-500/15 text-amber-300 border-amber-500/30", label: "Needs reply" };
  }
}

export function relativeTime(iso?: string | null): string {
  if (!iso) return "";
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "";
  const m = Math.floor((Date.now() - then) / 60000);
  if (m < 1) return "just now";
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

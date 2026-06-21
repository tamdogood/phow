// In-browser mock for the Reputation Hub so the UI + flows can be tested with NO backend.
// Enabled by NEXT_PUBLIC_REVIEWS_MOCK=1 (see reviews-api.ts). State persists in localStorage.
// Delete this file + the REVIEWS_MOCK guards in reviews-api.ts to remove mock mode.

import type {
  Review,
  ReviewConnection,
  ReviewDraft,
  ReviewAnalytics,
  Sentiment,
  InboxFilter,
} from "./reviews-api";

interface Store {
  connected: boolean;
  reviews: Review[];
}

const KEY = "phow_reviews_mock";
const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));
const iso = (daysAgo: number) => new Date(Date.now() - daysAgo * 86400000).toISOString();

function seed(): Store {
  return {
    connected: true,
    reviews: [
      {
        id: "mock-1", source: "google", external_review_id: "g1",
        author_name: "Marcus T.", author_photo_url: null, rating: 2,
        review_text: "Coffee was cold and we waited almost 20 minutes. Staff seemed overwhelmed.",
        review_created_at: iso(1), review_url: null,
        sentiment: "negative", themes: ["Service Speed", "Food Quality"],
        response_status: "needs_response", response_text: null, response_published_at: null,
      },
      {
        id: "mock-2", source: "google", external_review_id: "g2",
        author_name: "Priya S.", author_photo_url: null, rating: 5,
        review_text: "Best flat white in the neighborhood! Friendly staff and a cozy vibe.",
        review_created_at: iso(2), review_url: null,
        sentiment: "positive", themes: ["Staff Attitude"],
        response_status: "responded",
        response_text: "Thank you so much, Priya! See you again soon. ☕",
        response_published_at: iso(2),
      },
      {
        id: "mock-3", source: "google", external_review_id: "g3",
        author_name: "Dan W.", author_photo_url: null, rating: 4,
        review_text: "Great pastries and quick service. A little pricey but worth it.",
        review_created_at: iso(4), review_url: null,
        sentiment: "positive", themes: ["Pricing"],
        response_status: "needs_response", response_text: null, response_published_at: null,
      },
      {
        id: "mock-4", source: "google", external_review_id: "g4",
        author_name: "Lena K.", author_photo_url: null, rating: 3,
        review_text: "Loved the latte but the place was pretty dirty and tables weren't cleaned.",
        review_created_at: iso(6), review_url: null,
        sentiment: "mixed", themes: ["Cleanliness", "Food Quality"],
        response_status: "drafted", response_text: null, response_published_at: null,
      },
      {
        id: "mock-5", source: "google", external_review_id: "g5",
        author_name: "Anonymous", author_photo_url: null, rating: 1,
        review_text: "Rude barista, wrong order twice. Never coming back.",
        review_created_at: iso(9), review_url: null,
        sentiment: "negative", themes: ["Staff Attitude", "Order Accuracy"],
        response_status: "responded",
        response_text: "We're so sorry about this and have addressed it with our team.",
        response_published_at: iso(8),
      },
    ],
  };
}

function load(): Store {
  if (typeof window === "undefined") return seed();
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) return JSON.parse(raw) as Store;
  } catch {
    /* ignore */
  }
  const s = seed();
  save(s);
  return s;
}

function save(s: Store) {
  try {
    localStorage.setItem(KEY, JSON.stringify(s));
  } catch {
    /* ignore */
  }
}

function classify(text: string, rating?: number): { sentiment: Sentiment; themes: string[] } {
  const lower = (text || "").toLowerCase();
  const r = rating ?? 0;
  let sentiment: Sentiment = "neutral";
  if (r >= 4) sentiment = "positive";
  else if (r && r <= 2) sentiment = "negative";
  const map: Record<string, string[]> = {
    "Service Speed": ["slow", "wait", "forever", "long"],
    "Food Quality": ["cold", "delicious", "fresh", "stale", "quality", "tasty"],
    "Staff Attitude": ["rude", "friendly", "helpful", "ignored"],
    Cleanliness: ["dirty", "clean", "messy"],
    Pricing: ["expensive", "overpriced", "pricey", "value", "cheap"],
    "Order Accuracy": ["wrong order", "wrong", "mistake", "missing"],
  };
  const themes = Object.entries(map)
    .filter(([, kws]) => kws.some((k) => lower.includes(k)))
    .map(([theme]) => theme);
  return { sentiment, themes };
}

export async function fetchConnections(bid: string): Promise<ReviewConnection[]> {
  const s = load();
  if (!s.connected) return [];
  return [
    {
      id: "mock-conn",
      business_profile_id: bid,
      platform: "google",
      location_label: "Bean There Coffee (Demo)",
      status: "connected",
      last_sync_at: new Date().toISOString(),
      last_sync_status: "ok",
      last_error: null,
    },
  ];
}

export async function startGoogleConnect(): Promise<{ authorization_url: string }> {
  const s = load();
  s.connected = true;
  save(s);
  const path = typeof window !== "undefined" ? window.location.pathname : "/reviews";
  const bid =
    (typeof window !== "undefined" && new URLSearchParams(window.location.search).get("bid")) ||
    "demo";
  return { authorization_url: `${path}?bid=${bid}&connected=google` };
}

export async function deleteConnection(): Promise<void> {
  const s = load();
  s.connected = false;
  save(s);
}

export async function syncReviews(): Promise<{ synced: number; status: string }> {
  await delay(700);
  const s = load();
  if (!s.connected) return { synced: 0, status: "not_connected" };
  return { synced: s.reviews.filter((r) => r.source === "google").length, status: "ok" };
}

export async function fetchInbox(
  bid: string,
  filter: InboxFilter = "all",
  source?: string
): Promise<Review[]> {
  let rows = [...load().reviews];
  if (source) rows = rows.filter((r) => r.source === source);
  if (filter === "unreplied") rows = rows.filter((r) => r.response_status !== "responded");
  else if (filter === "negative")
    rows = rows.filter((r) => (r.rating ?? 5) <= 3 || r.sentiment === "negative");
  return rows.sort((a, b) => (b.review_created_at || "").localeCompare(a.review_created_at || ""));
}

export async function generateDrafts(reviewId: string): Promise<ReviewDraft[]> {
  await delay(900);
  const s = load();
  const review = s.reviews.find((r) => r.id === reviewId);
  if (review && review.response_status === "needs_response") {
    review.response_status = "drafted";
    save(s);
  }
  const name = review?.author_name || "there";
  return [
    {
      tone: "professional",
      text: `Thank you for your feedback, ${name}. We're sorry your visit fell short and we're addressing it with our team. Please reach out so we can make it right.`,
    },
    {
      tone: "friendly",
      text: `Hi ${name}, thanks so much for taking the time to share this! We'd love another chance to win you over — come say hi next time. 🙌`,
    },
    {
      tone: "apologetic",
      text: `We're truly sorry, ${name}. This isn't the standard we hold ourselves to. We'd really appreciate the chance to make it right — please contact us directly.`,
    },
  ];
}

export async function publishReply(reviewId: string, text: string): Promise<Review> {
  await delay(600);
  const s = load();
  const review = s.reviews.find((r) => r.id === reviewId);
  if (!review) throw new Error("Review not found");
  review.response_text = text;
  review.response_status = "responded";
  review.response_published_at = new Date().toISOString();
  save(s);
  return review;
}

export async function fetchAnalytics(): Promise<ReviewAnalytics> {
  const rows = load().reviews;
  const total = rows.length;
  const rated = rows.filter((r) => r.rating).map((r) => r.rating as number);
  const avg = (xs: number[]) =>
    xs.length ? Math.round((xs.reduce((a, b) => a + b, 0) / xs.length) * 100) / 100 : null;

  const sentiment: ReviewAnalytics["sentiment"] = { positive: 0, neutral: 0, mixed: 0, negative: 0 };
  for (const r of rows) {
    const k = (r.sentiment || "neutral") as keyof ReviewAnalytics["sentiment"];
    if (k in sentiment) sentiment[k] += 1;
  }

  const themeCounts: Record<string, number> = {};
  rows.forEach((r) => (r.themes || []).forEach((t) => (themeCounts[t] = (themeCounts[t] || 0) + 1)));
  const top_themes = Object.entries(themeCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([theme, count]) => ({ theme, count }));

  const now = Date.now();
  const recent: number[] = [];
  const prior: number[] = [];
  rows.forEach((r) => {
    if (!r.rating || !r.review_created_at) return;
    const age = (now - new Date(r.review_created_at).getTime()) / 86400000;
    if (age <= 30) recent.push(r.rating);
    else if (age <= 60) prior.push(r.rating);
  });

  const responded = rows.filter((r) => r.response_status === "responded").length;
  return {
    total_reviews: total,
    average_rating: avg(rated),
    needs_response: rows.filter((r) => r.response_status !== "responded").length,
    response_rate: total ? Math.round((responded / total) * 100) / 100 : 0,
    sentiment,
    top_themes,
    rating_trend: { recent_30d: avg(recent), prior_30d: avg(prior) },
  };
}

export async function addManualReview(payload: {
  business_profile_id: string;
  review_text: string;
  author_name?: string;
  rating?: number;
}): Promise<Review> {
  await delay(400);
  const s = load();
  const { sentiment, themes } = classify(payload.review_text, payload.rating);
  const review: Review = {
    id: `mock-${Date.now()}`,
    source: "manual",
    external_review_id: `manual-${Date.now()}`,
    author_name: payload.author_name || null,
    author_photo_url: null,
    rating: payload.rating ?? null,
    review_text: payload.review_text,
    review_created_at: new Date().toISOString(),
    review_url: null,
    sentiment,
    themes,
    response_status: "needs_response",
    response_text: null,
    response_published_at: null,
  };
  s.reviews.unshift(review);
  save(s);
  return review;
}

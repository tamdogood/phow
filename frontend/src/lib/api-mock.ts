// Dogfooding helper: serve /api/* from in-browser mock data so the whole app can be
// clicked through with NO backend. Enabled by NEXT_PUBLIC_API_MOCK=1.
// It patches window.fetch and leaves lib/api.ts untouched. Delete this file + the
// import in components/Providers.tsx to remove it.

import type {
  BusinessProfile,
  DashboardData,
  CommunityPost,
  PostComment,
  PostWithComments,
  Tool,
} from "@/types";

const ENABLED = process.env.NEXT_PUBLIC_API_MOCK === "1";

const now = () => new Date().toISOString();
const iso = (daysAgo: number) => new Date(Date.now() - daysAgo * 86400000).toISOString();
const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

// ---------------------------------------------------------------- mock data ----

const MOCK_PROFILE: BusinessProfile = {
  id: "demo-profile",
  session_id: "demo",
  business_name: "Bean There Coffee",
  business_type: "coffee_shop",
  business_description: "A cozy neighborhood specialty coffee shop.",
  target_customers: "Local professionals, students, remote workers",
  location_address: "500 W 2nd St, Austin, TX 78701",
  location_lat: 30.2672,
  location_lng: -97.7431,
  location_place_id: "demo-place",
  created_at: iso(30),
  updated_at: iso(1),
};

const MOCK_DASHBOARD: DashboardData = {
  has_profile: true,
  business_profile: MOCK_PROFILE,
  market_analysis: {
    id: "demo-ma",
    business_profile_id: "demo-profile",
    viability_score: 78,
    demographics: null,
    demand_indicators: null,
    competition_saturation: null,
    recommendations: ["Lean into a morning-rush special", "Launch a loyalty punch card"],
    risk_factors: ["Three competitors within 400m"],
    opportunities: ["No specialty roaster within 1km"],
    market_size_estimates: null,
    created_at: iso(5),
  },
  competitor_analysis: {
    id: "demo-ca",
    business_profile_id: "demo-profile",
    overall_competition_level: "moderate",
    positioning_data: null,
    market_gaps: null,
    differentiation_suggestions: ["Single-origin pour-overs", "Faster mobile pickup"],
    pricing_insights: {
      price_range: { min: 3, max: 6 },
      average_price_level: 2,
      notes: "Mid-market pricing is the norm on this block.",
    },
    sentiment_summary: {
      positive_themes: ["friendly staff", "cozy atmosphere"],
      negative_themes: ["slow at peak hours"],
    },
    created_at: iso(5),
  },
  tracked_competitors: [
    {
      id: "c1",
      business_profile_id: "demo-profile",
      place_id: "p1",
      name: "Rival Roasters",
      address: "410 W 2nd St, Austin, TX",
      rating: 4.3,
      review_count: 212,
      price_level: 2,
      strengths: ["fast service"],
      weaknesses: ["cramped seating"],
      created_at: iso(10),
    },
    {
      id: "c2",
      business_profile_id: "demo-profile",
      place_id: "p2",
      name: "Cafe Mocha",
      address: "120 Congress Ave, Austin, TX",
      rating: 4.6,
      review_count: 540,
      price_level: 3,
      strengths: ["great pastries"],
      weaknesses: ["pricey"],
      created_at: iso(10),
    },
  ],
  recent_conversations: [],
};

const MOCK_TOOLS: Tool[] = [
  { id: "market_research", name: "Market Research", description: "Validate demand and size your market.", icon: "📊" },
  { id: "market_validator", name: "Market Validator", description: "Score a location's viability for your business.", icon: "🎯" },
  { id: "social_media_coach", name: "Social Media Coach", description: "Content ideas tuned to your local market.", icon: "📱" },
  { id: "review_responder", name: "Review Responder", description: "Draft replies to customer reviews.", icon: "⭐" },
  { id: "business_advisor", name: "Business Advisor", description: "Ask anything about running your business.", icon: "💡" },
];

const MOCK_POSTS: CommunityPost[] = [
  {
    id: "post-1",
    session_id: "u1",
    user_id: null,
    business_profile_id: null,
    title: "How do you handle the morning rush?",
    content: "We get slammed 8–9am and wait times creep up. What's worked for you — mobile order, second register, pre-batching?",
    category: "operations",
    metadata: null,
    created_at: iso(2),
    updated_at: iso(2),
    business_profiles: { business_name: "Daily Grind", business_type: "coffee_shop" },
    comment_count: 3,
  },
  {
    id: "post-2",
    session_id: "u2",
    user_id: null,
    business_profile_id: null,
    title: "Best POS for a single location?",
    content: "Shopping around for a new point-of-sale. Square vs Toast vs Clover — what do you all use and why?",
    category: "tools",
    metadata: null,
    created_at: iso(4),
    updated_at: iso(4),
    business_profiles: { business_name: "Corner Cafe", business_type: "cafe" },
    comment_count: 1,
  },
];

function postWithComments(id: string): PostWithComments {
  const base = MOCK_POSTS.find((p) => p.id === id) || MOCK_POSTS[0];
  const comments: PostComment[] = [
    {
      id: "cm-1",
      post_id: base.id,
      session_id: "u9",
      user_id: null,
      business_profile_id: null,
      content: "Mobile order + a dedicated pickup shelf cut our peak wait in half.",
      created_at: iso(1),
      business_profiles: { business_name: "Steam & Bean", business_type: "coffee_shop" },
    },
  ];
  return { ...base, comments };
}

function newPost(body: Record<string, unknown>): CommunityPost {
  return {
    id: `post-${Date.now()}`,
    session_id: String(body.session_id ?? "demo"),
    user_id: null,
    business_profile_id: null,
    title: String(body.title ?? "Untitled"),
    content: String(body.content ?? ""),
    category: (body.category as string) ?? null,
    metadata: null,
    created_at: now(),
    updated_at: now(),
    business_profiles: { business_name: "Bean There Coffee", business_type: "coffee_shop" },
    comment_count: 0,
  };
}

function newComment(postId: string, body: Record<string, unknown>): PostComment {
  return {
    id: `cm-${Date.now()}`,
    post_id: postId,
    session_id: String(body.session_id ?? "demo"),
    user_id: null,
    business_profile_id: null,
    content: String(body.content ?? ""),
    created_at: now(),
    business_profiles: { business_name: "Bean There Coffee", business_type: "coffee_shop" },
  };
}

const MOCK_RADAR = {
  subscription: {
    id: "sub1",
    business_profile_id: "demo-profile",
    watch_topics: ["coffee Austin", "specialty cafe"],
    categories: ["competition", "local"],
    frequency: "daily",
    schedule_hour: 7,
    status: "active",
    last_scanned_at: iso(1),
  },
  alerts: [
    {
      id: "a1",
      title: "New specialty cafe opening two blocks away",
      category: "competition",
      severity: "watch",
      relevance_score: 0.82,
      why_it_matters: "A direct competitor is entering your catchment area.",
      suggested_action: "Lock in your morning regulars with a loyalty offer this month.",
      status: "new",
      created_at: iso(1),
      published_at: iso(1),
    },
    {
      id: "a2",
      title: "City approves 2nd Street patio permits",
      category: "local",
      severity: "info",
      relevance_score: 0.6,
      why_it_matters: "Outdoor seating could lift weekend foot traffic.",
      status: "new",
      created_at: iso(2),
      published_at: iso(2),
    },
  ],
  unread_count: 2,
  latest_scan: { id: "scan1", status: "completed", alerts_created: 2, completed_at: iso(1) },
};

// Embedded in the chat reply for the Market Validator tool (parsed by ChatMessage).
const MOCK_MARKET_DATA = {
  type: "market_data",
  location: { lat: 30.2672, lng: -97.7431, formatted_address: "500 W 2nd St, Austin, TX 78701" },
  business_type: "coffee shop",
  viability_score: 78,
  viability_level: "good",
  score_breakdown: { demographics_score: 82, competition_score: 68, foot_traffic_score: 84 },
  demographics_summary: {
    population: 24500,
    median_income: 86000,
    median_age: 33,
    college_educated_percent: 61,
  },
  competition_summary: { competitor_count: 7, saturation_level: "moderate", average_rating: 4.4 },
  foot_traffic_summary: { level: "high", transit_access: true, nearby_businesses: 142 },
  risk_factors: ["Three established competitors within 400m", "Rising downtown commercial rents"],
  opportunities: ["No specialty roaster within 1km", "High concentration of remote workers"],
  recommendations: [
    "Differentiate with single-origin pour-overs",
    "Capture the 7–9am commuter rush",
    "Add mobile order for peak throughput",
  ],
  top_competitors: [
    { name: "Rival Roasters", rating: 4.3, reviews: 212, address: "410 W 2nd St" },
    { name: "Cafe Mocha", rating: 4.6, reviews: 540, address: "120 Congress Ave" },
    { name: "Steam & Bean", rating: 4.1, reviews: 98, address: "200 Lavaca St" },
  ],
};

// ---------------------------------------------------------------- routing ----

function parseBody(init?: RequestInit): Record<string, unknown> {
  if (!init?.body || typeof init.body !== "string") return {};
  try {
    return JSON.parse(init.body);
  } catch {
    return {};
  }
}

function jsonResponse(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function chatStream(body: Record<string, unknown>): Response {
  const encoder = new TextEncoder();
  const toolId = String(body.tool_id ?? "");
  const segments =
    toolId === "market_validator"
      ? [
          "Here's the market validation for a **coffee shop** near 500 W 2nd St, Austin. ",
          "Overall this spot looks **viable (78/100)** — strong demographics and foot traffic, moderate competition.\n\n",
          `<!--MARKET_DATA:${JSON.stringify(MOCK_MARKET_DATA)}-->`,
        ]
      : [
          "Thanks for trying the demo! ",
          "This is a mocked assistant reply ",
          "so you can see the chat UI working without a backend.",
        ];
  const stream = new ReadableStream({
    async start(controller) {
      for (const s of segments) {
        controller.enqueue(encoder.encode(`event: chunk\ndata: ${JSON.stringify({ content: s })}\n\n`));
        await delay(180);
      }
      controller.enqueue(
        encoder.encode(`event: done\ndata: ${JSON.stringify({ conversation_id: "demo-convo" })}\n\n`)
      );
      controller.close();
    },
  });
  return new Response(stream, { status: 200, headers: { "Content-Type": "text/event-stream" } });
}

function route(method: string, path: string, body: Record<string, unknown>): unknown {
  if (method === "GET" && path === "/api/tools") return MOCK_TOOLS; // backend returns a bare array

  if (method === "GET" && path === "/api/dashboard") return MOCK_DASHBOARD;
  if (method === "POST" && path === "/api/dashboard/analyze") return { ...MOCK_DASHBOARD, analyzed: true };

  if (path === "/api/business-profile" && method === "GET") return { profile: MOCK_PROFILE };
  if (path === "/api/business-profile" && method === "POST")
    return { profile: { ...MOCK_PROFILE, ...body, id: MOCK_PROFILE.id, updated_at: now() } };
  if (path === "/api/business-profile/resolve-maps-url" && method === "POST")
    return {
      place: {
        place_id: "demo-place",
        name: "Bean There Coffee",
        lat: 30.2672,
        lng: -97.7431,
        rating: 4.5,
        user_ratings_total: 128,
      },
    };
  if (path === "/api/business-profile/competitors" && method === "POST")
    return { competitor: { id: `comp-${Date.now()}`, name: String(body.name ?? "Competitor") } };
  if (/^\/api\/business-profile\/competitors\/[^/]+$/.test(path) && method === "DELETE")
    return { deleted: true };

  if (path === "/api/community/posts" && method === "GET") return { posts: MOCK_POSTS };
  if (path === "/api/community/posts" && method === "POST") return { post: newPost(body) };
  const post = path.match(/^\/api\/community\/posts\/([^/]+)$/);
  if (post && method === "GET") return { post: postWithComments(post[1]) };
  if (post && method === "PATCH") return { post: { ...postWithComments(post[1]), ...body } };
  if (post && method === "DELETE") return {};
  const comments = path.match(/^\/api\/community\/posts\/([^/]+)\/comments$/);
  if (comments && method === "POST") return { comment: newComment(comments[1], body) };
  if (/^\/api\/community\/comments\/[^/]+$/.test(path) && method === "DELETE") return {};

  if (path === "/api/chat/conversations" && method === "GET") return { conversations: [] };
  if (/^\/api\/chat\/conversations\/[^/]+\/messages$/.test(path) && method === "GET")
    return { messages: [] };
  const title = path.match(/^\/api\/chat\/conversations\/([^/]+)\/title$/);
  if (title && method === "PATCH")
    return {
      conversation: {
        id: title[1],
        session_id: "demo",
        tool_id: "market_research",
        title: String(body.title ?? "Renamed"),
        created_at: iso(1),
        updated_at: now(),
      },
    };

  if (path === "/api/radar/feed" && method === "GET") return MOCK_RADAR;
  if (path === "/api/search-grid/reports" && method === "GET") return { reports: [] };

  return null; // unmatched → empty 200 so nothing throws
}

async function handle(method: string, path: string, init?: RequestInit): Promise<Response> {
  if (method === "POST" && path === "/api/chat") return chatStream(parseBody(init));
  const data = route(method, path, parseBody(init));
  await delay(120);
  return jsonResponse(data ?? {});
}

let installed = false;

export function installApiMock() {
  if (!ENABLED || installed || typeof window === "undefined") return;
  installed = true;
  const original = window.fetch.bind(window);
  window.fetch = (async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    try {
      const url =
        typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
      const method = (
        init?.method || (input instanceof Request ? input.method : "GET")
      ).toUpperCase();
      const { pathname } = new URL(url, window.location.origin);
      if (pathname.startsWith("/api/")) return handle(method, pathname, init);
    } catch {
      /* fall through to real fetch */
    }
    return original(input, init);
  }) as typeof fetch;
  // eslint-disable-next-line no-console
  console.info("[api-mock] enabled — /api/* served from in-browser mock data");
}

installApiMock();

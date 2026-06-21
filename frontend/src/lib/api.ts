import {
  Tool,
  Message,
  Conversation,
  BusinessProfile,
  DashboardData,
  CommunityPost,
  PostWithComments,
  PostComment,
  Review,
  ReviewConnection,
  ReviewResponseDraft,
  ReviewAnalyticsSummary,
  ReviewTrendPoint,
  ThemeMetric,
  PlatformMetric,
  CompetitorComparison,
  ReviewNotification,
  AlertSettings,
  UsageSummary,
  SearchGridReport,
  SearchGridReportWithResults,
  SearchGridResult,
  SearchGridResultDetail,
  AggregatedCompetitor,
} from "@/types";

const ENV_API_URL = process.env.NEXT_PUBLIC_API_URL?.trim() || "";

function resolveApiUrl(): string {
  // In the browser, always prefer Next.js same-origin proxy rewrites (`/api/*`).
  // This avoids CORS/mixed-content/localhost-origin mismatches in dev and prod.
  if (typeof window !== "undefined") return "";
  if (!ENV_API_URL) return "http://localhost:8000";
  return ENV_API_URL.replace(/\/$/, "");
}

const API_URL = resolveApiUrl();

export async function fetchTools(): Promise<Tool[]> {
  const response = await fetch(`${API_URL}/api/tools`);
  if (!response.ok) {
    throw new Error(`Failed to fetch tools (${response.status})`);
  }
  const data = await response.json();
  if (Array.isArray(data)) {
    return data as Tool[];
  }
  return data.tools || [];
}

export async function fetchConversations(
  sessionId: string,
  userId?: string
): Promise<Conversation[]> {
  const params = new URLSearchParams({ session_id: sessionId });
  if (userId) params.append("user_id", userId);
  try {
    const response = await fetch(
      `${API_URL}/api/chat/conversations?${params.toString()}`
    );
    if (!response.ok) {
      throw new Error(`Failed to fetch conversations (${response.status})`);
    }
    const data = await response.json();
    return data.conversations || [];
  } catch (error) {
    if (process.env.NODE_ENV !== "production") {
      console.warn("Conversation list unavailable:", error);
    }
    return [];
  }
}

export async function fetchMessages(
  conversationId: string
): Promise<Message[]> {
  const response = await fetch(
    `${API_URL}/api/chat/conversations/${conversationId}/messages`
  );
  const data = await response.json();
  return data.messages;
}

export async function updateConversationTitle(
  conversationId: string,
  title: string
): Promise<Conversation> {
  const response = await fetch(
    `${API_URL}/api/chat/conversations/${conversationId}/title?title=${encodeURIComponent(title)}`,
    { method: "PATCH" }
  );
  const data = await response.json();
  return data.conversation;
}

export interface ChatStreamCallbacks {
  onChunk: (content: string) => void;
  onDone: (conversationId: string) => void;
  onError: (error: string) => void;
}

export async function sendChatMessage(
  sessionId: string,
  toolId: string,
  message: string,
  conversationId: string | null,
  callbacks: ChatStreamCallbacks,
  userId?: string
): Promise<void> {
  const response = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      session_id: sessionId,
      conversation_id: conversationId,
      tool_id: toolId,
      message,
      user_id: userId,
    }),
  });

  if (!response.ok) {
    callbacks.onError("Failed to send message");
    return;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    callbacks.onError("No response body");
    return;
  }

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("event:")) {
        continue;
      }
      if (line.startsWith("data:")) {
        try {
          const data = JSON.parse(line.slice(5).trim());
          if (data.content) {
            callbacks.onChunk(data.content);
          }
          if (data.conversation_id) {
            callbacks.onDone(data.conversation_id);
          }
          if (data.error) {
            callbacks.onError(data.error);
          }
        } catch {
          // Ignore parse errors
        }
      }
    }
  }
}

export interface BusinessProfileInput {
  session_id: string;
  user_id?: string;
  business_name: string;
  business_type: string;
  location_address: string;
  google_maps_place_id?: string;
  target_customers?: string;
  business_description?: string;
}

export async function saveBusinessProfile(
  data: BusinessProfileInput
): Promise<BusinessProfile> {
  const response = await fetch(`${API_URL}/api/business-profile`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error("Failed to save business profile");
  }
  const result = await response.json();
  return result.profile;
}

export async function getBusinessProfile(
  identifier: string,
  type: "session" | "user" = "session"
): Promise<BusinessProfile | null> {
  const param = type === "user" ? `user_id=${identifier}` : `session_id=${identifier}`;
  const response = await fetch(`${API_URL}/api/business-profile?${param}`);
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error("Failed to fetch business profile");
  }
  const result = await response.json();
  return result.profile;
}

export async function resolveMapsUrl(
  url: string
): Promise<{ place_id: string | null; name: string | null; lat: number; lng: number; rating?: number; user_ratings_total?: number }> {
  const response = await fetch(`${API_URL}/api/business-profile/resolve-maps-url`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
  await throwIfNotOk(response);
  const data = await response.json();
  return data.place;
}

export async function getDashboard(
  sessionId?: string,
  userId?: string
): Promise<DashboardData> {
  const params = new URLSearchParams();
  if (sessionId) params.append("session_id", sessionId);
  if (userId) params.append("user_id", userId);

  try {
    const response = await fetch(`${API_URL}/api/dashboard?${params.toString()}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch dashboard data (${response.status})`);
    }
    return response.json();
  } catch (error) {
    throw new Error("Failed to fetch dashboard data", {
      cause: error,
    });
  }
}

export async function triggerDashboardAnalysis(
  sessionId?: string,
  userId?: string
): Promise<DashboardData & { analyzed: boolean }> {
  const params = new URLSearchParams();
  if (sessionId) params.append("session_id", sessionId);
  if (userId) params.append("user_id", userId);

  const response = await fetch(`${API_URL}/api/dashboard/analyze?${params.toString()}`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error("Failed to trigger analysis");
  }
  return response.json();
}

export async function getCommunityFeed(
  limit = 20,
  offset = 0,
  category?: string,
  search?: string,
  sortBy?: string
): Promise<CommunityPost[]> {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (category) params.append("category", category);
  if (search) params.append("search", search);
  if (sortBy) params.append("sort_by", sortBy);
  const response = await fetch(`${API_URL}/api/community/posts?${params.toString()}`);
  if (!response.ok) throw new Error("Failed to fetch community feed");
  const data = await response.json();
  return data.posts;
}

export async function getPost(postId: string): Promise<PostWithComments> {
  const response = await fetch(`${API_URL}/api/community/posts/${postId}`);
  if (!response.ok) throw new Error("Failed to fetch post");
  const data = await response.json();
  return data.post;
}

export async function createPost(
  sessionId: string,
  title: string,
  content: string,
  category?: string
): Promise<CommunityPost> {
  const response = await fetch(`${API_URL}/api/community/posts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, title, content, category }),
  });
  if (!response.ok) throw new Error("Failed to create post");
  const data = await response.json();
  return data.post;
}

export async function addComment(
  postId: string,
  sessionId: string,
  content: string
): Promise<PostComment> {
  const response = await fetch(`${API_URL}/api/community/posts/${postId}/comments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, content }),
  });
  if (!response.ok) throw new Error("Failed to add comment");
  const data = await response.json();
  return data.comment;
}

export async function updatePost(
  postId: string,
  sessionId: string,
  title?: string,
  content?: string
): Promise<CommunityPost> {
  const response = await fetch(`${API_URL}/api/community/posts/${postId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, title, content }),
  });
  if (!response.ok) throw new Error("Failed to update post");
  const data = await response.json();
  return data.post;
}

export async function deletePost(postId: string, sessionId: string): Promise<void> {
  const response = await fetch(`${API_URL}/api/community/posts/${postId}`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  });
  if (!response.ok) throw new Error("Failed to delete post");
}

export async function deleteComment(commentId: string, sessionId: string): Promise<void> {
  const response = await fetch(`${API_URL}/api/community/comments/${commentId}`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  });
  if (!response.ok) throw new Error("Failed to delete comment");
}

export interface AddCompetitorInput {
  session_id: string;
  name: string;
  place_id?: string;
  address?: string;
  rating?: number;
  review_count?: number;
  price_level?: number;
}

export async function addCompetitor(data: AddCompetitorInput): Promise<{ id: string; name: string }> {
  const response = await fetch(`${API_URL}/api/business-profile/competitors`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error("Failed to add competitor");
  const result = await response.json();
  return result.competitor;
}

export async function deleteCompetitor(competitorId: string, sessionId: string): Promise<void> {
  const response = await fetch(`${API_URL}/api/business-profile/competitors/${competitorId}`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  });
  if (!response.ok) throw new Error("Failed to delete competitor");
}

interface ReputationActor {
  session_id: string;
  user_id?: string;
}

function extractApiError(payload: unknown): string {
  if (typeof payload === "object" && payload !== null) {
    const directError = (payload as { error?: { message?: string } }).error;
    if (directError?.message) return directError.message;

    const detail = (payload as { detail?: { error?: { message?: string } } | string }).detail;
    if (typeof detail === "string") return detail;
    if (detail?.error?.message) return detail.error.message;
  }
  return "Request failed";
}

async function throwIfNotOk(response: Response): Promise<void> {
  if (response.ok) return;
  const payload = await response.json().catch(() => ({}));
  throw new Error(extractApiError(payload));
}

export async function fetchReviewConnections(sessionId: string, userId?: string): Promise<ReviewConnection[]> {
  const params = new URLSearchParams({ session_id: sessionId });
  if (userId) params.append("user_id", userId);
  const response = await fetch(`${API_URL}/api/reviews/connections?${params.toString()}`);
  await throwIfNotOk(response);
  const data = await response.json();
  return data.connections;
}

export async function startReviewConnection(
  source: "google" | "yelp" | "meta",
  actor: ReputationActor,
  search?: { query?: string; lat?: number; lng?: number }
): Promise<Record<string, unknown>> {
  const response = await fetch(`${API_URL}/api/reviews/connections/${source}/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...actor, ...search }),
  });
  await throwIfNotOk(response);
  return response.json();
}

export async function callbackReviewConnection(
  source: "google" | "yelp" | "meta",
  actor: ReputationActor,
  code: string,
  state?: string
): Promise<Record<string, unknown>> {
  const response = await fetch(`${API_URL}/api/reviews/connections/${source}/callback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...actor, code, state }),
  });
  await throwIfNotOk(response);
  return response.json();
}

export async function disconnectReviewConnection(
  source: "google" | "yelp" | "meta",
  actor: ReputationActor
): Promise<Record<string, unknown>> {
  const response = await fetch(`${API_URL}/api/reviews/connections/${source}`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(actor),
  });
  await throwIfNotOk(response);
  return response.json();
}

export async function syncReviews(
  actor: ReputationActor,
  source?: "google" | "yelp" | "meta"
): Promise<Record<string, unknown>> {
  const response = await fetch(`${API_URL}/api/reviews/sync`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...actor, source, mode: "manual" }),
  });
  await throwIfNotOk(response);
  return response.json();
}

export interface ReviewInboxFilters {
  sessionId: string;
  userId?: string;
  source?: "google" | "yelp" | "meta";
  sentiment?: "positive" | "neutral" | "negative";
  unrepliedOnly?: boolean;
  minRating?: number;
  maxRating?: number;
  search?: string;
  cursor?: string;
  limit?: number;
}

export async function fetchReviewInbox(filters: ReviewInboxFilters): Promise<{ items: Review[]; next_cursor: string | null }> {
  const params = new URLSearchParams({ session_id: filters.sessionId });
  if (filters.userId) params.append("user_id", filters.userId);
  if (filters.source) params.append("source", filters.source);
  if (filters.sentiment) params.append("sentiment", filters.sentiment);
  if (filters.unrepliedOnly) params.append("unreplied_only", "true");
  if (filters.minRating !== undefined) params.append("min_rating", String(filters.minRating));
  if (filters.maxRating !== undefined) params.append("max_rating", String(filters.maxRating));
  if (filters.search) params.append("search", filters.search);
  if (filters.cursor) params.append("cursor", filters.cursor);
  if (filters.limit) params.append("limit", String(filters.limit));

  const response = await fetch(`${API_URL}/api/reviews/inbox?${params.toString()}`);
  await throwIfNotOk(response);
  return response.json();
}

export async function fetchReviewDetail(
  reviewId: string,
  sessionId: string,
  userId?: string
): Promise<{ review: Review; sentiment: Review["sentiment"] | null }> {
  const params = new URLSearchParams({ session_id: sessionId });
  if (userId) params.append("user_id", userId);
  const response = await fetch(`${API_URL}/api/reviews/${reviewId}?${params.toString()}`);
  await throwIfNotOk(response);
  return response.json();
}

export async function generateReviewDrafts(
  reviewId: string,
  actor: ReputationActor,
  plan?: string
): Promise<ReviewResponseDraft[]> {
  const response = await fetch(`${API_URL}/api/reviews/${reviewId}/draft`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...actor, plan }),
  });
  await throwIfNotOk(response);
  const data = await response.json();
  return data.drafts;
}

export async function publishReviewResponse(
  reviewId: string,
  actor: ReputationActor,
  responseText: string,
  tone: "professional" | "friendly" | "apologetic",
  idempotencyKey: string
): Promise<Record<string, unknown>> {
  const response = await fetch(`${API_URL}/api/reviews/${reviewId}/publish`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ...actor,
      response_text: responseText,
      tone,
      idempotency_key: idempotencyKey,
    }),
  });
  await throwIfNotOk(response);
  return response.json();
}

export async function fetchReviewAnalyticsSummary(
  sessionId: string,
  userId?: string,
  days = 30
): Promise<ReviewAnalyticsSummary> {
  const params = new URLSearchParams({ session_id: sessionId, days: String(days) });
  if (userId) params.append("user_id", userId);
  const response = await fetch(`${API_URL}/api/reviews/analytics/summary?${params.toString()}`);
  await throwIfNotOk(response);
  return response.json();
}

export async function fetchReviewAnalyticsTrends(
  sessionId: string,
  userId?: string,
  days = 30
): Promise<ReviewTrendPoint[]> {
  const params = new URLSearchParams({ session_id: sessionId, days: String(days) });
  if (userId) params.append("user_id", userId);
  const response = await fetch(`${API_URL}/api/reviews/analytics/trends?${params.toString()}`);
  await throwIfNotOk(response);
  const data = await response.json();
  return data.points;
}

export async function fetchReviewAnalyticsThemes(
  sessionId: string,
  userId?: string,
  days = 30
): Promise<ThemeMetric[]> {
  const params = new URLSearchParams({ session_id: sessionId, days: String(days) });
  if (userId) params.append("user_id", userId);
  const response = await fetch(`${API_URL}/api/reviews/analytics/themes?${params.toString()}`);
  await throwIfNotOk(response);
  const data = await response.json();
  return data.themes;
}

export async function fetchReviewAnalyticsPlatforms(
  sessionId: string,
  userId?: string,
  days = 30
): Promise<PlatformMetric[]> {
  const params = new URLSearchParams({ session_id: sessionId, days: String(days) });
  if (userId) params.append("user_id", userId);
  const response = await fetch(`${API_URL}/api/reviews/analytics/platforms?${params.toString()}`);
  await throwIfNotOk(response);
  const data = await response.json();
  return data.platforms;
}

export async function fetchReviewCompetitors(
  sessionId: string,
  userId?: string
): Promise<CompetitorComparison[]> {
  const params = new URLSearchParams({ session_id: sessionId });
  if (userId) params.append("user_id", userId);
  const response = await fetch(`${API_URL}/api/reviews/competitors?${params.toString()}`);
  await throwIfNotOk(response);
  const data = await response.json();
  return data.items;
}

export async function fetchReviewNotifications(
  sessionId: string,
  userId?: string,
  unreadOnly = false
): Promise<{ items: ReviewNotification[]; unread_count: number }> {
  const params = new URLSearchParams({ session_id: sessionId, unread_only: String(unreadOnly) });
  if (userId) params.append("user_id", userId);
  const response = await fetch(`${API_URL}/api/reviews/notifications?${params.toString()}`);
  await throwIfNotOk(response);
  return response.json();
}

export async function markReviewNotificationRead(
  notificationId: string,
  actor: ReputationActor
): Promise<void> {
  const response = await fetch(`${API_URL}/api/reviews/notifications/${notificationId}/read`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(actor),
  });
  await throwIfNotOk(response);
}

export async function markAllReviewNotificationsRead(actor: ReputationActor): Promise<number> {
  const response = await fetch(`${API_URL}/api/reviews/notifications/read-all`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(actor),
  });
  await throwIfNotOk(response);
  const data = await response.json();
  return data.updated_count ?? 0;
}

export async function fetchReviewAlertSettings(
  sessionId: string,
  userId?: string
): Promise<AlertSettings> {
  const params = new URLSearchParams({ session_id: sessionId });
  if (userId) params.append("user_id", userId);
  const response = await fetch(`${API_URL}/api/reviews/alerts/settings?${params.toString()}`);
  await throwIfNotOk(response);
  return response.json();
}

export async function updateReviewAlertSettings(
  actor: ReputationActor,
  settings: AlertSettings
): Promise<AlertSettings> {
  const response = await fetch(`${API_URL}/api/reviews/alerts/settings`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...actor, ...settings }),
  });
  await throwIfNotOk(response);
  return response.json();
}

export async function fetchReviewUsage(
  sessionId: string,
  userId?: string,
  plan?: string
): Promise<UsageSummary> {
  const params = new URLSearchParams({ session_id: sessionId });
  if (userId) params.append("user_id", userId);
  if (plan) params.append("plan", plan);
  const response = await fetch(`${API_URL}/api/reviews/usage?${params.toString()}`);
  await throwIfNotOk(response);
  return response.json();
}

// Search Grid API

export interface CreateSearchGridReportInput {
  business_profile_id: string;
  name: string;
  keywords: string[];
  radius_km?: number;
  grid_size?: number;
  frequency?: string;
  schedule_day?: number;
  schedule_hour?: number;
  timezone?: string;
  notify_email?: string;
}

export async function createSearchGridReport(
  data: CreateSearchGridReportInput
): Promise<SearchGridReport> {
  const response = await fetch(`${API_URL}/api/search-grid/reports`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  await throwIfNotOk(response);
  const result = await response.json();
  return result.report;
}

export async function fetchSearchGridReports(
  profileId: string
): Promise<SearchGridReport[]> {
  const response = await fetch(
    `${API_URL}/api/search-grid/reports?profile_id=${profileId}`
  );
  await throwIfNotOk(response);
  const data = await response.json();
  return data.reports;
}

export async function fetchSearchGridReport(
  id: string
): Promise<SearchGridReportWithResults> {
  const response = await fetch(`${API_URL}/api/search-grid/reports/${id}`);
  await throwIfNotOk(response);
  const data = await response.json();
  return data.report;
}

export async function updateSearchGridReport(
  id: string,
  data: Partial<CreateSearchGridReportInput>
): Promise<SearchGridReport> {
  const response = await fetch(`${API_URL}/api/search-grid/reports/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  await throwIfNotOk(response);
  const result = await response.json();
  return result.report;
}

export async function deleteSearchGridReport(id: string): Promise<void> {
  const response = await fetch(`${API_URL}/api/search-grid/reports/${id}`, {
    method: "DELETE",
  });
  await throwIfNotOk(response);
}

export async function triggerSearchGridRun(
  reportId: string
): Promise<{ report_id: string; status: string }> {
  const response = await fetch(
    `${API_URL}/api/search-grid/reports/${reportId}/run`,
    { method: "POST" }
  );
  await throwIfNotOk(response);
  return response.json();
}

export async function fetchSearchGridResultDetail(
  resultId: string
): Promise<SearchGridResultDetail> {
  const response = await fetch(
    `${API_URL}/api/search-grid/results/${resultId}`
  );
  await throwIfNotOk(response);
  const data = await response.json();
  return data.result;
}

export async function fetchSearchGridRunResults(
  runId: string,
  keyword?: string
): Promise<SearchGridResult[]> {
  const params = new URLSearchParams();
  if (keyword) params.append("keyword", keyword);
  const qs = params.toString() ? `?${params.toString()}` : "";
  const response = await fetch(
    `${API_URL}/api/search-grid/runs/${runId}/results${qs}`
  );
  await throwIfNotOk(response);
  const data = await response.json();
  return data.results;
}

export async function fetchSearchGridCompetitors(
  runId: string,
  keyword?: string
): Promise<AggregatedCompetitor[]> {
  const params = new URLSearchParams();
  if (keyword) params.append("keyword", keyword);
  const qs = params.toString() ? `?${params.toString()}` : "";
  const response = await fetch(
    `${API_URL}/api/search-grid/runs/${runId}/competitors${qs}`
  );
  await throwIfNotOk(response);
  const data = await response.json();
  return data.competitors;
}

export interface Tool {
  id: string;
  name: string;
  description: string;
  icon: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  metadata?: Record<string, unknown>;
  created_at: string;
}

export interface Conversation {
  id: string;
  session_id: string;
  tool_id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}

export interface BusinessProfile {
  id: string;
  session_id: string;
  business_name: string | null;
  business_type: string;
  business_description: string | null;
  target_customers: string | null;
  location_address: string | null;
  created_at: string;
  updated_at: string;
}

export interface TrackedCompetitor {
  id: string;
  business_profile_id: string;
  place_id: string;
  name: string;
  address: string | null;
  rating: number | null;
  review_count: number | null;
  price_level: number | null;
  strengths: string[] | null;
  weaknesses: string[] | null;
  created_at: string;
}

export interface MarketAnalysis {
  id: string;
  business_profile_id: string;
  viability_score: number;
  demographics: Record<string, unknown> | null;
  demand_indicators: Record<string, unknown> | null;
  competition_saturation: Record<string, unknown> | null;
  recommendations: string[] | null;
  risk_factors: string[] | null;
  opportunities: string[] | null;
  market_size_estimates: Record<string, unknown> | null;
  created_at: string;
}

export interface CompetitorAnalysis {
  id: string;
  business_profile_id: string;
  overall_competition_level: string;
  positioning_data: Record<string, unknown> | null;
  market_gaps: Record<string, unknown> | null;
  differentiation_suggestions: string[] | null;
  pricing_insights: {
    price_range?: { min: number; max: number };
    average_price_level?: number;
    notes?: string;
  } | null;
  sentiment_summary: {
    positive_themes?: string[];
    negative_themes?: string[];
  } | null;
  created_at: string;
}

export interface DashboardData {
  has_profile: boolean;
  business_profile: BusinessProfile | null;
  market_analysis: MarketAnalysis | null;
  competitor_analysis: CompetitorAnalysis | null;
  tracked_competitors: TrackedCompetitor[];
  recent_conversations: Conversation[];
}

export interface PostAuthor {
  business_name: string | null;
  business_type: string | null;
}

export interface CommunityPost {
  id: string;
  session_id: string;
  user_id: string | null;
  business_profile_id: string | null;
  title: string;
  content: string;
  category: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
  business_profiles: PostAuthor | null;
  comment_count: number;
}

export interface PostComment {
  id: string;
  post_id: string;
  session_id: string;
  user_id: string | null;
  business_profile_id: string | null;
  content: string;
  created_at: string;
  business_profiles: PostAuthor | null;
}

export interface PostWithComments extends CommunityPost {
  comments: PostComment[];
}

export type ReviewSource = "google" | "yelp" | "meta";

export interface ReviewSentiment {
  sentiment_label: "positive" | "neutral" | "negative";
  sentiment_score: number;
  themes: string[];
}

export interface Review {
  id: string;
  source: ReviewSource;
  external_review_id: string;
  external_url: string | null;
  reviewer_name: string | null;
  rating: number;
  title: string | null;
  content: string | null;
  review_created_at: string | null;
  reply_status: "unreplied" | "replied";
  response_published_at: string | null;
  sentiment?: ReviewSentiment | null;
}

export interface ReviewResponseDraft {
  id: string;
  review_id: string;
  tone: "professional" | "friendly" | "apologetic";
  draft_text: string;
  edited_text: string | null;
  status: string;
}

export interface ReviewConnection {
  source: ReviewSource;
  status: "disconnected" | "pending" | "connected";
  connected_at: string | null;
  last_synced_at: string | null;
  last_error: string | null;
  has_refresh_token: boolean;
  metadata: Record<string, unknown>;
}

export interface ReviewNotification {
  id: string;
  review_id: string | null;
  type: string;
  title: string;
  body: string;
  is_read: boolean;
  created_at: string;
}

export interface AlertSettings {
  low_rating_threshold: number;
  instant_low_rating_enabled: boolean;
  daily_digest_enabled: boolean;
}

export interface ReviewAnalyticsSummary {
  window_days: number;
  total_reviews: number;
  replied_reviews: number;
  response_rate: number;
  avg_rating: number;
  sentiment_distribution: Record<string, number>;
}

export interface ReviewTrendPoint {
  date: string;
  review_count: number;
  avg_rating: number;
  positive_count: number;
  negative_count: number;
}

export interface ThemeMetric {
  theme: string;
  count: number;
}

export interface PlatformMetric {
  source: ReviewSource | string;
  review_count: number;
  avg_rating: number;
  response_rate: number;
}

export interface CompetitorComparison {
  id: string;
  name: string;
  rating: number | null;
  review_count: number | null;
  price_level: number | null;
  address: string | null;
}

export interface UsageSummary {
  plan: string;
  monthly_limit: number;
  used: number;
  remaining: number;
  over_limit: boolean;
  period_start: string;
}

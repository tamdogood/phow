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
  location_lat: number | null;
  location_lng: number | null;
  location_place_id: string | null;
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

export interface SearchGridReport {
  id: string;
  business_profile_id: string;
  name: string;
  center_lat: number;
  center_lng: number;
  center_address: string | null;
  place_id: string | null;
  radius_km: number;
  grid_size: number;
  keywords: string[];
  frequency: string;
  status: string;
  last_run_at: string | null;
  created_at: string;
}

export interface SearchGridRun {
  id: string;
  report_id: string;
  status: string;
  avg_rank: number | null;
  avg_score: number | null;
  top3_pct: number | null;
  points_completed: number;
  points_total: number;
  started_at: string;
  completed_at: string | null;
}

export interface SearchGridResult {
  id: string;
  keyword: string;
  grid_row: number;
  grid_col: number;
  point_lat: number;
  point_lng: number;
  rank: number | null;
  total_results: number;
  top_result_name: string | null;
  score: number | null;
}

export interface NearbyPlace {
  name: string;
  place_id: string;
  rating: number | null;
  user_ratings_total: number | null;
  vicinity: string | null;
  lat: number | null;
  lng: number | null;
  business_status: string | null;
}

export interface SearchGridResultDetail extends SearchGridResult {
  nearby_places: NearbyPlace[] | null;
}

export interface AggregatedCompetitor {
  name: string;
  place_id: string;
  avg_rank: number;
  appearances: number;
  total_points: number;
  rating: number | null;
  user_ratings_total: number | null;
}

export interface SearchGridReportWithResults extends SearchGridReport {
  latest_run: SearchGridRun | null;
  results: SearchGridResult[];
}

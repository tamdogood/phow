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
  created_at: string;
}

export interface CompetitorAnalysis {
  id: string;
  business_profile_id: string;
  overall_competition_level: string;
  positioning_data: Record<string, unknown> | null;
  market_gaps: Record<string, unknown> | null;
  differentiation_suggestions: string[] | null;
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

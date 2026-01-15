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

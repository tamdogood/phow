"use client";

import { useMemo } from "react";
import { cn } from "@/lib/utils";
import { MapWidget } from "./MapWidget";
import { MarketValidatorWidget } from "../tools/MarketValidatorWidget";
import { CompetitorWidget, PositioningWidget } from "../tools/CompetitorWidget";
import { SocialMediaCoachWidget } from "../tools/SocialMediaCoachWidget";

interface LocationData {
  type: "location_data";
  location: {
    lat: number;
    lng: number;
    formatted_address?: string;
    place_id?: string;
  };
  competitors?: Array<{ name: string; rating?: number; vicinity?: string }>;
  transit_stations?: Array<{ name: string; vicinity?: string }>;
  nearby_food?: Array<{ name: string; rating?: number }>;
  nearby_retail?: Array<{ name: string; rating?: number }>;
  analysis_summary?: {
    competitor_count?: number;
    transit_access?: boolean;
    foot_traffic_indicators?: number;
  };
}

interface MarketData {
  type: "market_data";
  location?: {
    lat: number;
    lng: number;
    formatted_address?: string;
  };
  business_type: string;
  viability_score: number;
  viability_level: string;
  score_breakdown: {
    demographics_score: number;
    competition_score: number;
    foot_traffic_score: number;
  };
  demographics_summary: {
    population?: number;
    median_income?: number;
    median_age?: number;
    college_educated_percent?: number;
  };
  competition_summary: {
    competitor_count?: number;
    saturation_level?: string;
    average_rating?: number;
  };
  foot_traffic_summary: {
    level?: string;
    transit_access?: boolean;
    nearby_businesses?: number;
  };
  risk_factors: string[];
  opportunities: string[];
  recommendations: string[];
  top_competitors: Array<{
    name: string;
    rating?: number;
    reviews?: number;
    address?: string;
  }>;
}

interface CompetitorData {
  type: "competitor_data";
  location?: {
    lat: number;
    lng: number;
    formatted_address?: string;
  };
  business_type: string;
  total_found: number;
  competitors: Array<{
    name: string;
    rating?: number;
    review_count?: number;
    address?: string;
    price_level?: number;
    yelp_price?: string;
    categories?: string[];
    source?: string;
  }>;
  sources?: {
    google?: number;
    yelp?: number;
  };
}

interface PositioningData {
  type: "positioning_data";
  location?: {
    lat: number;
    lng: number;
    formatted_address?: string;
  };
  business_type: string;
  positioning_data: Array<{
    name: string;
    rating: number;
    price_level: number;
    review_count: number;
    quadrant: string;
  }>;
  quadrant_analysis: {
    premium?: number;
    value?: number;
    economy?: number;
    avoid?: number;
  };
  market_gaps: string[];
  recommendation?: string;
}

interface SocialContentData {
  type: "social_content";
  location?: {
    lat: number;
    lng: number;
    city?: string;
    state?: string;
    country?: string;
    timezone?: string;
  };
  weather?: {
    temperature?: number;
    feels_like?: number;
    humidity?: number;
    description?: string;
    icon?: string;
    impact?: {
      sentiment?: string;
      opportunities?: string[];
      content_suggestions?: string[];
    };
  };
  events?: {
    holidays?: Array<{
      name: string;
      date: string;
      type: string;
    }>;
    daily_themes?: Array<{
      name: string;
      hashtag: string;
      description?: string;
    }>;
    local_events?: Array<{
      name: string;
      date?: string;
      venue?: string;
      type?: string;
    }>;
  };
  hashtags?: {
    trending?: string[];
    industry?: string[];
    local?: string[];
    seasonal?: string[];
  };
  posting_times?: {
    platform?: string;
    best_times?: Array<{
      day: string;
      times: string[];
    }>;
    timezone?: string;
  };
}

interface ParsedContent {
  text: string;
  locationData: LocationData | null;
  marketData: MarketData | null;
  competitorData: CompetitorData | null;
  positioningData: PositioningData | null;
  socialContentData: SocialContentData | null;
}

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
  isStreaming?: boolean;
}

function parseContent(content: string): ParsedContent {
  let text = content;
  let locationData: LocationData | null = null;
  let marketData: MarketData | null = null;
  let competitorData: CompetitorData | null = null;
  let positioningData: PositioningData | null = null;
  let socialContentData: SocialContentData | null = null;

  // Parse location data
  const locationMatch = text.match(/<!--LOCATION_DATA:(.*?)-->/s);
  if (locationMatch) {
    try {
      locationData = JSON.parse(locationMatch[1]) as LocationData;
      text = text.replace(/<!--LOCATION_DATA:.*?-->/s, "").trim();
    } catch {
      // Ignore parse errors
    }
  }

  // Parse market data
  const marketMatch = text.match(/<!--MARKET_DATA:(.*?)-->/s);
  if (marketMatch) {
    try {
      marketData = JSON.parse(marketMatch[1]) as MarketData;
      text = text.replace(/<!--MARKET_DATA:.*?-->/s, "").trim();
    } catch {
      // Ignore parse errors
    }
  }

  // Parse competitor data
  const competitorMatch = text.match(/<!--COMPETITOR_DATA:(.*?)-->/s);
  if (competitorMatch) {
    try {
      competitorData = JSON.parse(competitorMatch[1]) as CompetitorData;
      text = text.replace(/<!--COMPETITOR_DATA:.*?-->/s, "").trim();
    } catch {
      // Ignore parse errors
    }
  }

  // Parse positioning data
  const positioningMatch = text.match(/<!--POSITIONING_DATA:(.*?)-->/s);
  if (positioningMatch) {
    try {
      positioningData = JSON.parse(positioningMatch[1]) as PositioningData;
      text = text.replace(/<!--POSITIONING_DATA:.*?-->/s, "").trim();
    } catch {
      // Ignore parse errors
    }
  }

  // Parse social content data
  const socialContentMatch = text.match(/<!--SOCIAL_CONTENT_DATA:(.*?)-->/s);
  if (socialContentMatch) {
    try {
      socialContentData = JSON.parse(socialContentMatch[1]) as SocialContentData;
      text = text.replace(/<!--SOCIAL_CONTENT_DATA:.*?-->/s, "").trim();
    } catch {
      // Ignore parse errors
    }
  }

  return { text, locationData, marketData, competitorData, positioningData, socialContentData };
}

export function ChatMessage({ role, content, isStreaming }: ChatMessageProps) {
  const { text, locationData, marketData, competitorData, positioningData, socialContentData } = useMemo(
    () => parseContent(content),
    [content]
  );

  return (
    <div
      className={cn(
        "flex w-full flex-col",
        role === "user" ? "items-end" : "items-start"
      )}
    >
      {/* Map widget for location data */}
      {locationData && role === "assistant" && (
        <div className="w-full max-w-[90%] mb-2">
          <MapWidget
            location={locationData.location}
            competitors={locationData.competitors}
            transitStations={locationData.transit_stations}
          />
        </div>
      )}

      {/* Market Validator widget */}
      {marketData && role === "assistant" && (
        <div className="w-full max-w-[90%] mb-2">
          <MarketValidatorWidget data={marketData} />
        </div>
      )}

      {/* Competitor widget */}
      {competitorData && role === "assistant" && (
        <div className="w-full max-w-[90%] mb-2">
          <CompetitorWidget data={competitorData} />
        </div>
      )}

      {/* Positioning widget */}
      {positioningData && role === "assistant" && (
        <div className="w-full max-w-[90%] mb-2">
          <PositioningWidget data={positioningData} />
        </div>
      )}

      {/* Social Media Coach widget */}
      {socialContentData && role === "assistant" && (
        <div className="w-full max-w-[90%] mb-2">
          <SocialMediaCoachWidget data={socialContentData} />
        </div>
      )}

      {/* Message bubble */}
      {text && (
        <div
          className={cn(
            "max-w-[80%] rounded-2xl px-4 py-3",
            role === "user"
              ? "bg-gradient-to-r from-sky-500 to-blue-600 text-white shadow-lg shadow-sky-500/20"
              : "glass-card text-slate-100"
          )}
        >
          <div className="whitespace-pre-wrap text-sm leading-relaxed">
            {text}
            {isStreaming && (
              <span className="inline-block w-2 h-4 ml-1 bg-sky-400 animate-pulse rounded-sm" />
            )}
          </div>
        </div>
      )}
    </div>
  );
}

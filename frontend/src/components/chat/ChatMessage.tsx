"use client";

import { useMemo } from "react";
import { cn } from "@/lib/utils";
import { MapWidget } from "./MapWidget";

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

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
  isStreaming?: boolean;
}

function parseLocationData(content: string): { text: string; locationData: LocationData | null } {
  const locationMatch = content.match(/<!--LOCATION_DATA:(.*?)-->/s);
  if (locationMatch) {
    try {
      const locationData = JSON.parse(locationMatch[1]) as LocationData;
      const text = content.replace(/<!--LOCATION_DATA:.*?-->/s, "").trim();
      return { text, locationData };
    } catch {
      return { text: content, locationData: null };
    }
  }
  return { text: content, locationData: null };
}

export function ChatMessage({ role, content, isStreaming }: ChatMessageProps) {
  const { text, locationData } = useMemo(() => parseLocationData(content), [content]);

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
            nearbyFood={locationData.nearby_food}
            nearbyRetail={locationData.nearby_retail}
          />
        </div>
      )}

      {/* Message bubble */}
      {text && (
        <div
          className={cn(
            "max-w-[80%] rounded-2xl px-4 py-3",
            role === "user"
              ? "bg-blue-600 text-white"
              : "bg-gray-100 text-gray-900"
          )}
        >
          <div className="whitespace-pre-wrap text-sm leading-relaxed">
            {text}
            {isStreaming && (
              <span className="inline-block w-2 h-4 ml-1 bg-current animate-pulse" />
            )}
          </div>
        </div>
      )}
    </div>
  );
}

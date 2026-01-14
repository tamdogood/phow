"use client";

import { useMemo } from "react";

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

interface CompetitorWidgetProps {
  data: CompetitorData;
}

interface PositioningWidgetProps {
  data: PositioningData;
}

function RatingBadge({ rating }: { rating?: number }) {
  if (!rating) return <span className="text-gray-400 text-xs">No rating</span>;

  const color =
    rating >= 4.5
      ? "bg-green-100 text-green-800"
      : rating >= 4.0
        ? "bg-green-50 text-green-700"
        : rating >= 3.5
          ? "bg-yellow-100 text-yellow-800"
          : "bg-orange-100 text-orange-800";

  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${color}`}>
      ★ {rating.toFixed(1)}
    </span>
  );
}

function PriceBadge({ level, priceStr }: { level?: number; priceStr?: string }) {
  const price = priceStr || (level ? "$".repeat(level) : null);
  if (!price) return null;

  return (
    <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
      {price}
    </span>
  );
}

export function CompetitorWidget({ data }: CompetitorWidgetProps) {
  const sortedCompetitors = useMemo(() => {
    return [...data.competitors].sort(
      (a, b) => (b.review_count || 0) - (a.review_count || 0)
    );
  }, [data.competitors]);

  const formatNumber = (value?: number) => {
    if (!value) return "0";
    return new Intl.NumberFormat("en-US").format(value);
  };

  return (
    <div className="w-full bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden my-3">
      {/* Header */}
      <div className="bg-gradient-to-r from-orange-500 to-red-500 px-4 py-3">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-white font-semibold">Competitor Analysis</h3>
            <p className="text-orange-100 text-sm">
              {data.business_type} near {data.location?.formatted_address || "location"}
            </p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-white">{data.total_found}</div>
            <span className="text-orange-100 text-xs">competitors found</span>
          </div>
        </div>
      </div>

      {/* Source breakdown */}
      {data.sources && (
        <div className="px-4 py-2 bg-gray-50 border-b border-gray-100 flex gap-4 text-xs text-gray-600">
          {data.sources.google && (
            <span>Google: {data.sources.google} results</span>
          )}
          {data.sources.yelp && (
            <span>Yelp: {data.sources.yelp} results</span>
          )}
        </div>
      )}

      {/* Competitors list */}
      <div className="divide-y divide-gray-100 max-h-96 overflow-y-auto">
        {sortedCompetitors.map((competitor, idx) => (
          <div
            key={idx}
            className="px-4 py-3 hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-900 truncate">
                    {competitor.name}
                  </span>
                  <RatingBadge rating={competitor.rating} />
                  <PriceBadge
                    level={competitor.price_level}
                    priceStr={competitor.yelp_price}
                  />
                </div>
                {competitor.address && (
                  <p className="text-xs text-gray-500 mt-0.5 truncate">
                    {competitor.address}
                  </p>
                )}
                {competitor.categories && competitor.categories.length > 0 && (
                  <div className="flex gap-1 mt-1 flex-wrap">
                    {competitor.categories.slice(0, 3).map((cat, catIdx) => (
                      <span
                        key={catIdx}
                        className="text-xs bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded"
                      >
                        {cat}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              <div className="text-right ml-4">
                <div className="text-sm font-medium text-gray-900">
                  {formatNumber(competitor.review_count)}
                </div>
                <div className="text-xs text-gray-500">reviews</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Summary */}
      <div className="px-4 py-3 bg-gray-50 border-t border-gray-100">
        <div className="text-xs text-gray-600">
          Top competitor:{" "}
          <span className="font-medium text-gray-900">
            {sortedCompetitors[0]?.name}
          </span>{" "}
          with {formatNumber(sortedCompetitors[0]?.review_count)} reviews
        </div>
      </div>
    </div>
  );
}

export function PositioningWidget({ data }: PositioningWidgetProps) {
  const quadrantLabels = {
    premium: { label: "Premium", color: "bg-purple-100 text-purple-800", desc: "High Quality, High Price" },
    value: { label: "Value", color: "bg-green-100 text-green-800", desc: "High Quality, Moderate Price" },
    economy: { label: "Economy", color: "bg-blue-100 text-blue-800", desc: "Moderate Quality, Low Price" },
    avoid: { label: "Risky", color: "bg-red-100 text-red-800", desc: "Low Quality, High Price" },
  };

  return (
    <div className="w-full bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden my-3">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 px-4 py-3">
        <h3 className="text-white font-semibold">Competitive Positioning Map</h3>
        <p className="text-purple-100 text-sm">
          Price vs. Quality analysis for {data.business_type}
        </p>
      </div>

      {/* Quadrant Analysis */}
      <div className="px-4 py-4 border-b border-gray-100">
        <h4 className="text-sm font-medium text-gray-700 mb-3">Market Segments</h4>
        <div className="grid grid-cols-2 gap-3">
          {Object.entries(data.quadrant_analysis).map(([quadrant, count]) => {
            const info = quadrantLabels[quadrant as keyof typeof quadrantLabels];
            return (
              <div
                key={quadrant}
                className={`rounded-lg p-3 ${info.color}`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium">{info.label}</span>
                  <span className="text-lg font-bold">{count}</span>
                </div>
                <div className="text-xs opacity-75">{info.desc}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Competitors by Quadrant */}
      <div className="px-4 py-4 border-b border-gray-100">
        <h4 className="text-sm font-medium text-gray-700 mb-3">Competitor Positioning</h4>
        <div className="space-y-2">
          {data.positioning_data.slice(0, 8).map((comp, idx) => {
            const info = quadrantLabels[comp.quadrant as keyof typeof quadrantLabels];
            return (
              <div
                key={idx}
                className="flex items-center justify-between bg-gray-50 rounded-lg px-3 py-2"
              >
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-900">{comp.name}</span>
                  <span className={`text-xs px-1.5 py-0.5 rounded ${info.color}`}>
                    {info.label}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-xs text-gray-600">
                  <span>★ {comp.rating.toFixed(1)}</span>
                  <span>{"$".repeat(comp.price_level)}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Market Gaps */}
      {data.market_gaps.length > 0 && (
        <div className="px-4 py-4 border-b border-gray-100">
          <h4 className="text-sm font-medium text-green-700 mb-2 flex items-center gap-1">
            <span className="w-2 h-2 bg-green-500 rounded-full"></span>
            Market Gaps & Opportunities
          </h4>
          <ul className="space-y-1">
            {data.market_gaps.map((gap, idx) => (
              <li key={idx} className="text-xs text-gray-600 flex items-start gap-2">
                <span className="text-green-500 mt-0.5">→</span>
                {gap}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Recommendation */}
      {data.recommendation && (
        <div className="px-4 py-4 bg-indigo-50">
          <h4 className="text-sm font-medium text-indigo-800 mb-1">Strategic Recommendation</h4>
          <p className="text-xs text-indigo-700">{data.recommendation}</p>
        </div>
      )}
    </div>
  );
}

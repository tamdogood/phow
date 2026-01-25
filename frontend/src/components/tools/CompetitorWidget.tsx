"use client";

import { useMemo } from "react";
import { Tag, Lightbulb, TrendingUp } from "lucide-react";
import { RatingDisplay } from "../widgets/RatingDisplay";
import { PriceLevel } from "../widgets/PriceLevel";

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

function SourceBadge({ source }: { source?: string }) {
  if (!source) return null;

  const config = {
    google: { label: "Google", color: "bg-blue-500/20 text-blue-400 border-blue-500/30" },
    yelp: { label: "Yelp", color: "bg-red-500/20 text-red-400 border-red-500/30" },
  };

  const sourceConfig = config[source.toLowerCase() as keyof typeof config];
  if (!sourceConfig) return null;

  return (
    <span className={`text-xs px-2 py-0.5 rounded border ${sourceConfig.color}`}>
      {sourceConfig.label}
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
    <div className="w-full widget-card overflow-hidden my-3">
      {/* Header */}
      <div className="bg-gradient-to-r from-orange-500 to-red-500 px-4 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-white font-semibold text-lg">Competitor Analysis</h3>
            <p className="text-orange-100 text-sm">
              {data.business_type} near {data.location?.formatted_address || "location"}
            </p>
          </div>
          <div className="text-right">
            <div className="text-4xl font-bold text-white">{data.total_found}</div>
            <span className="text-orange-100 text-xs">competitors found</span>
          </div>
        </div>
      </div>

      {/* Source breakdown */}
      {data.sources && (
        <div className="px-4 py-3 bg-slate-800/50 border-b border-slate-800 flex gap-4 text-xs">
          {data.sources.google && (
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
              <span className="text-slate-300">Google: {data.sources.google}</span>
            </div>
          )}
          {data.sources.yelp && (
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-red-400 rounded-full"></div>
              <span className="text-slate-300">Yelp: {data.sources.yelp}</span>
            </div>
          )}
        </div>
      )}

      {/* Competitors list */}
      <div className="divide-y divide-slate-800 max-h-96 overflow-y-auto custom-scrollbar">
        {sortedCompetitors.map((competitor, idx) => (
          <div
            key={idx}
            className="px-4 py-3 hover:bg-slate-800/50 transition-colors"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-2">
                  <span className="font-medium text-white truncate">
                    {competitor.name}
                  </span>
                  <SourceBadge source={competitor.source} />
                </div>

                <div className="flex items-center gap-3 mb-2">
                  {competitor.rating && (
                    <RatingDisplay
                      rating={competitor.rating}
                      reviewCount={competitor.review_count}
                      size="sm"
                      showNumeric={false}
                    />
                  )}
                  {(competitor.price_level || competitor.yelp_price) && (
                    <PriceLevel
                      level={competitor.price_level || (competitor.yelp_price?.length || 0)}
                      size="sm"
                    />
                  )}
                </div>

                {competitor.address && (
                  <p className="text-xs text-slate-500 mb-2 truncate">
                    {competitor.address}
                  </p>
                )}

                {competitor.categories && competitor.categories.length > 0 && (
                  <div className="flex gap-1 flex-wrap">
                    {competitor.categories.slice(0, 3).map((cat, catIdx) => (
                      <span
                        key={catIdx}
                        className="text-xs bg-slate-700 text-slate-300 px-2 py-0.5 rounded border border-slate-600"
                      >
                        {cat}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div className="text-right flex-shrink-0">
                <div className="text-sm font-medium text-white">
                  {formatNumber(competitor.review_count)}
                </div>
                <div className="text-xs text-slate-500">reviews</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Summary */}
      <div className="px-4 py-3 bg-slate-800/50 border-t border-slate-800">
        <div className="text-xs text-slate-300">
          Top competitor:{" "}
          <span className="font-medium text-white">
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
    premium: { label: "Premium", color: "bg-purple-500/20 text-purple-400 border-purple-500/30", desc: "High Quality, High Price" },
    value: { label: "Value", color: "bg-green-500/20 text-green-400 border-green-500/30", desc: "High Quality, Moderate Price" },
    economy: { label: "Economy", color: "bg-blue-500/20 text-blue-400 border-blue-500/30", desc: "Moderate Quality, Low Price" },
    avoid: { label: "Risky", color: "bg-red-500/20 text-red-400 border-red-500/30", desc: "Low Quality, High Price" },
  };

  return (
    <div className="w-full widget-card overflow-hidden my-3">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 px-4 py-4">
        <h3 className="text-white font-semibold text-lg">Competitive Positioning Map</h3>
        <p className="text-purple-100 text-sm">
          Price vs. Quality analysis for {data.business_type}
        </p>
      </div>

      {/* Quadrant Analysis */}
      <div className="px-4 py-4 border-b border-slate-800">
        <h4 className="text-sm font-medium text-slate-300 mb-3">Market Segments</h4>
        <div className="grid grid-cols-2 gap-3">
          {Object.entries(data.quadrant_analysis).map(([quadrant, count]) => {
            const info = quadrantLabels[quadrant as keyof typeof quadrantLabels];
            return (
              <div
                key={quadrant}
                className={`rounded-lg p-3 border ${info.color}`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium">{info.label}</span>
                  <span className="text-2xl font-bold">{count}</span>
                </div>
                <div className="text-xs opacity-75">{info.desc}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Competitors by Quadrant */}
      <div className="px-4 py-4 border-b border-slate-800">
        <h4 className="text-sm font-medium text-slate-300 mb-3">Competitor Positioning</h4>
        <div className="space-y-2">
          {data.positioning_data.slice(0, 8).map((comp, idx) => {
            const info = quadrantLabels[comp.quadrant as keyof typeof quadrantLabels];
            return (
              <div
                key={idx}
                className="flex items-center justify-between bg-slate-800 rounded-lg px-3 py-2 border border-slate-700 hover:border-slate-600 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-white">{comp.name}</span>
                  <span className={`text-xs px-2 py-0.5 rounded border ${info.color}`}>
                    {info.label}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <RatingDisplay rating={comp.rating} size="sm" showNumeric={false} />
                  <PriceLevel level={comp.price_level} size="sm" />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Market Gaps */}
      {data.market_gaps.length > 0 && (
        <div className="px-4 py-4 border-b border-slate-800">
          <h4 className="text-sm font-medium text-green-400 mb-3 flex items-center gap-2">
            <Lightbulb className="w-4 h-4" />
            Market Gaps & Opportunities
          </h4>
          <div className="space-y-2">
            {data.market_gaps.map((gap, idx) => (
              <div
                key={idx}
                className="text-sm text-slate-300 pl-3 py-2 border-l-2 border-green-500 bg-green-500/5 rounded-r"
              >
                {gap}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendation */}
      {data.recommendation && (
        <div className="px-4 py-4 bg-indigo-500/10 border-t border-indigo-500/20">
          <h4 className="text-sm font-medium text-indigo-400 mb-2 flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            Strategic Recommendation
          </h4>
          <p className="text-sm text-slate-300">{data.recommendation}</p>
        </div>
      )}
    </div>
  );
}

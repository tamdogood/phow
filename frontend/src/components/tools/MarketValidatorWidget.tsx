"use client";

import { useMemo } from "react";

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

interface MarketValidatorWidgetProps {
  data: MarketData;
}

function ScoreGauge({ score, label }: { score: number; label: string }) {
  const getColor = (s: number) => {
    if (s >= 70) return "text-green-600";
    if (s >= 50) return "text-yellow-600";
    if (s >= 35) return "text-orange-500";
    return "text-red-500";
  };

  const getBgColor = (s: number) => {
    if (s >= 70) return "bg-green-100";
    if (s >= 50) return "bg-yellow-100";
    if (s >= 35) return "bg-orange-100";
    return "bg-red-100";
  };

  return (
    <div className="flex flex-col items-center">
      <div
        className={`relative w-20 h-20 rounded-full ${getBgColor(score)} flex items-center justify-center`}
      >
        <span className={`text-2xl font-bold ${getColor(score)}`}>{score}</span>
      </div>
      <span className="text-xs text-gray-600 mt-1">{label}</span>
    </div>
  );
}

function StatCard({
  label,
  value,
  subtext,
}: {
  label: string;
  value: string | number;
  subtext?: string;
}) {
  return (
    <div className="bg-gray-50 rounded-lg p-3">
      <div className="text-xs text-gray-500 uppercase tracking-wide">{label}</div>
      <div className="text-lg font-semibold text-gray-900">{value}</div>
      {subtext && <div className="text-xs text-gray-500">{subtext}</div>}
    </div>
  );
}

export function MarketValidatorWidget({ data }: MarketValidatorWidgetProps) {
  const levelColor = useMemo(() => {
    switch (data.viability_level) {
      case "excellent":
        return "bg-green-100 text-green-800";
      case "good":
        return "bg-green-50 text-green-700";
      case "moderate":
        return "bg-yellow-100 text-yellow-800";
      case "challenging":
        return "bg-orange-100 text-orange-800";
      default:
        return "bg-red-100 text-red-800";
    }
  }, [data.viability_level]);

  const formatCurrency = (value?: number) => {
    if (!value) return "N/A";
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatNumber = (value?: number) => {
    if (!value) return "N/A";
    return new Intl.NumberFormat("en-US").format(value);
  };

  return (
    <div className="w-full bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden my-3">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-4 py-3">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-white font-semibold">Market Viability Report</h3>
            <p className="text-blue-100 text-sm">
              {data.business_type} at {data.location?.formatted_address || "Location"}
            </p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-white">{data.viability_score}</div>
            <span className={`text-xs px-2 py-0.5 rounded-full ${levelColor}`}>
              {data.viability_level.toUpperCase()}
            </span>
          </div>
        </div>
      </div>

      {/* Score Breakdown */}
      <div className="px-4 py-4 border-b border-gray-100">
        <h4 className="text-sm font-medium text-gray-700 mb-3">Score Breakdown</h4>
        <div className="flex justify-around">
          <ScoreGauge
            score={data.score_breakdown.demographics_score}
            label="Demographics"
          />
          <ScoreGauge
            score={data.score_breakdown.competition_score}
            label="Competition"
          />
          <ScoreGauge
            score={data.score_breakdown.foot_traffic_score}
            label="Foot Traffic"
          />
        </div>
      </div>

      {/* Key Metrics */}
      <div className="px-4 py-4 border-b border-gray-100">
        <h4 className="text-sm font-medium text-gray-700 mb-3">Key Metrics</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          <StatCard
            label="Population"
            value={formatNumber(data.demographics_summary.population)}
          />
          <StatCard
            label="Median Income"
            value={formatCurrency(data.demographics_summary.median_income)}
          />
          <StatCard
            label="Competitors"
            value={data.competition_summary.competitor_count ?? "N/A"}
            subtext={data.competition_summary.saturation_level}
          />
          <StatCard
            label="Foot Traffic"
            value={data.foot_traffic_summary.level?.replace("_", " ") || "N/A"}
            subtext={data.foot_traffic_summary.transit_access ? "Transit nearby" : "No transit"}
          />
        </div>
      </div>

      {/* Opportunities & Risks */}
      <div className="px-4 py-4 border-b border-gray-100">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Opportunities */}
          {data.opportunities.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-green-700 mb-2 flex items-center gap-1">
                <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                Opportunities
              </h4>
              <ul className="space-y-1">
                {data.opportunities.map((opp, idx) => (
                  <li key={idx} className="text-xs text-gray-600 flex items-start gap-1">
                    <span className="text-green-500 mt-0.5">+</span>
                    {opp}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Risks */}
          {data.risk_factors.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-red-700 mb-2 flex items-center gap-1">
                <span className="w-2 h-2 bg-red-500 rounded-full"></span>
                Risk Factors
              </h4>
              <ul className="space-y-1">
                {data.risk_factors.map((risk, idx) => (
                  <li key={idx} className="text-xs text-gray-600 flex items-start gap-1">
                    <span className="text-red-500 mt-0.5">!</span>
                    {risk}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      {/* Competitors */}
      {data.top_competitors.length > 0 && (
        <div className="px-4 py-4 border-b border-gray-100">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Top Competitors</h4>
          <div className="space-y-2">
            {data.top_competitors.slice(0, 3).map((comp, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between bg-gray-50 rounded-lg px-3 py-2"
              >
                <div>
                  <div className="text-sm font-medium text-gray-900">{comp.name}</div>
                  {comp.address && (
                    <div className="text-xs text-gray-500">{comp.address}</div>
                  )}
                </div>
                <div className="text-right">
                  {comp.rating && (
                    <div className="flex items-center gap-1">
                      <span className="text-yellow-500">★</span>
                      <span className="text-sm font-medium">{comp.rating}</span>
                    </div>
                  )}
                  {comp.reviews && (
                    <div className="text-xs text-gray-500">
                      {formatNumber(comp.reviews)} reviews
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {data.recommendations.length > 0 && (
        <div className="px-4 py-4 bg-blue-50">
          <h4 className="text-sm font-medium text-blue-800 mb-2">Recommendations</h4>
          <ul className="space-y-1">
            {data.recommendations.map((rec, idx) => (
              <li key={idx} className="text-xs text-blue-700 flex items-start gap-2">
                <span className="text-blue-500 font-bold">{idx + 1}.</span>
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

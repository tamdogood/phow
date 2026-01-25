"use client";

import { useMemo } from "react";
import { Users, DollarSign, Store, TrendingUp, AlertCircle, CheckCircle } from "lucide-react";
import { ScoreCard } from "../widgets/ScoreCard";
import { RatingDisplay } from "../widgets/RatingDisplay";

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

function MetricCard({
  icon: Icon,
  label,
  value,
  subtext,
  iconColor,
  iconBgColor,
}: {
  icon: React.ElementType;
  label: string;
  value: string | number;
  subtext?: string;
  iconColor: string;
  iconBgColor: string;
}) {
  return (
    <div className="bg-slate-800 rounded-lg p-3 border border-slate-700">
      <div className="flex items-start gap-2 mb-2">
        <div className={`metric-icon-badge ${iconBgColor}`}>
          <Icon className={`w-4 h-4 ${iconColor}`} />
        </div>
        <div className="text-xs text-slate-400 uppercase tracking-wide">{label}</div>
      </div>
      <div className="text-lg font-semibold text-white">{value}</div>
      {subtext && <div className="text-xs text-slate-500 mt-1">{subtext}</div>}
    </div>
  );
}

export function MarketValidatorWidget({ data }: MarketValidatorWidgetProps) {
  const levelColor = useMemo(() => {
    switch (data.viability_level) {
      case "excellent":
        return "bg-green-500/20 text-green-400 border-green-500/30";
      case "good":
        return "bg-green-500/20 text-green-400 border-green-500/30";
      case "moderate":
        return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30";
      case "challenging":
        return "bg-orange-500/20 text-orange-400 border-orange-500/30";
      default:
        return "bg-red-500/20 text-red-400 border-red-500/30";
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
    <div className="w-full widget-card overflow-hidden my-3">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-4 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-white font-semibold text-lg">Market Viability Report</h3>
            <p className="text-blue-100 text-sm">
              {data.business_type} at {data.location?.formatted_address || "Location"}
            </p>
          </div>
          <div className="text-right">
            <div className="text-4xl font-bold text-white">{data.viability_score}</div>
            <span className={`text-xs px-3 py-1 rounded-full border ${levelColor}`}>
              {data.viability_level.toUpperCase()}
            </span>
          </div>
        </div>
      </div>

      {/* Score Breakdown with Progress Bars */}
      <div className="px-4 py-4 border-b border-slate-800">
        <h4 className="text-sm font-medium text-slate-300 mb-3">Score Breakdown</h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <ScoreCard
            score={data.score_breakdown.demographics_score}
            maxScore={100}
            label="Demographics"
          />
          <ScoreCard
            score={data.score_breakdown.competition_score}
            maxScore={100}
            label="Competition"
          />
          <ScoreCard
            score={data.score_breakdown.foot_traffic_score}
            maxScore={100}
            label="Foot Traffic"
          />
        </div>
      </div>

      {/* Key Metrics */}
      <div className="px-4 py-4 border-b border-slate-800">
        <h4 className="text-sm font-medium text-slate-300 mb-3">Key Metrics</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <MetricCard
            icon={Users}
            label="Population"
            value={formatNumber(data.demographics_summary.population)}
            iconColor="text-purple-400"
            iconBgColor="bg-purple-500/20"
          />
          <MetricCard
            icon={DollarSign}
            label="Median Income"
            value={formatCurrency(data.demographics_summary.median_income)}
            iconColor="text-green-400"
            iconBgColor="bg-green-500/20"
          />
          <MetricCard
            icon={Store}
            label="Competitors"
            value={data.competition_summary.competitor_count ?? "N/A"}
            subtext={data.competition_summary.saturation_level}
            iconColor="text-orange-400"
            iconBgColor="bg-orange-500/20"
          />
          <MetricCard
            icon={TrendingUp}
            label="Foot Traffic"
            value={data.foot_traffic_summary.level?.replace("_", " ") || "N/A"}
            subtext={data.foot_traffic_summary.transit_access ? "Transit nearby" : "No transit"}
            iconColor="text-blue-400"
            iconBgColor="bg-blue-500/20"
          />
        </div>
      </div>

      {/* Opportunities & Risks */}
      <div className="px-4 py-4 border-b border-slate-800">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Opportunities */}
          {data.opportunities.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-green-400 mb-3 flex items-center gap-2">
                <CheckCircle className="w-4 h-4" />
                Opportunities
              </h4>
              <div className="space-y-2">
                {data.opportunities.map((opp, idx) => (
                  <div
                    key={idx}
                    className="text-sm text-slate-300 pl-3 py-2 border-l-2 border-green-500 bg-green-500/5 rounded-r"
                  >
                    {opp}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Risks */}
          {data.risk_factors.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-red-400 mb-3 flex items-center gap-2">
                <AlertCircle className="w-4 h-4" />
                Risk Factors
              </h4>
              <div className="space-y-2">
                {data.risk_factors.map((risk, idx) => (
                  <div
                    key={idx}
                    className="text-sm text-slate-300 pl-3 py-2 border-l-2 border-red-500 bg-red-500/5 rounded-r"
                  >
                    {risk}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Competitors */}
      {data.top_competitors.length > 0 && (
        <div className="px-4 py-4 border-b border-slate-800">
          <h4 className="text-sm font-medium text-slate-300 mb-3">Top Competitors</h4>
          <div className="space-y-2">
            {data.top_competitors.slice(0, 3).map((comp, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between bg-slate-800 rounded-lg px-3 py-3 border border-slate-700 hover:border-slate-600 transition-colors"
              >
                <div className="flex-1">
                  <div className="text-sm font-medium text-white">{comp.name}</div>
                  {comp.address && (
                    <div className="text-xs text-slate-500 mt-1">{comp.address}</div>
                  )}
                </div>
                <div className="ml-4">
                  {comp.rating && (
                    <RatingDisplay
                      rating={comp.rating}
                      reviewCount={comp.reviews}
                      size="sm"
                    />
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {data.recommendations.length > 0 && (
        <div className="px-4 py-4 bg-blue-500/10 border-t border-blue-500/20">
          <h4 className="text-sm font-medium text-blue-400 mb-3 flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            Recommendations
          </h4>
          <ul className="space-y-2">
            {data.recommendations.map((rec, idx) => (
              <li key={idx} className="text-sm text-slate-300 flex items-start gap-3">
                <span className="text-blue-400 font-bold text-base">{idx + 1}.</span>
                <span className="flex-1">{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

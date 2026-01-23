"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import { getDashboard } from "@/lib/api";
import { getSessionId } from "@/lib/session";
import { DashboardData, TrackedCompetitor } from "@/types";

function ScoreCard({
  label,
  value,
  subtext,
  color,
}: {
  label: string;
  value: string | number;
  subtext?: string;
  color?: "green" | "yellow" | "red" | "blue";
}) {
  const colorClasses = {
    green: "text-emerald-400",
    yellow: "text-amber-400",
    red: "text-red-400",
    blue: "text-blue-400",
  };

  return (
    <div className="dark-card p-6 text-center hover-lift">
      <p className="text-white/50 text-sm mb-2">{label}</p>
      <p className={`text-3xl font-bold ${color ? colorClasses[color] : "text-white"}`}>
        {value}
      </p>
      {subtext && <p className="text-white/30 text-xs mt-1">{subtext}</p>}
    </div>
  );
}

function CompetitorCard({ competitor }: { competitor: TrackedCompetitor }) {
  const [expanded, setExpanded] = useState(false);
  const hasDetails =
    (competitor.strengths && competitor.strengths.length > 0) ||
    (competitor.weaknesses && competitor.weaknesses.length > 0);

  const priceLevel = competitor.price_level
    ? "$".repeat(competitor.price_level)
    : null;

  return (
    <div className="py-3 border-b border-white/5 last:border-0">
      <div
        className={`flex items-center justify-between ${hasDetails ? "cursor-pointer" : ""}`}
        onClick={() => hasDetails && setExpanded(!expanded)}
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className="text-white font-medium">{competitor.name}</p>
            {priceLevel && (
              <span className="text-emerald-400 text-sm">{priceLevel}</span>
            )}
          </div>
          {competitor.address && (
            <p className="text-white/40 text-sm truncate max-w-xs">{competitor.address}</p>
          )}
        </div>
        <div className="flex items-center gap-3">
          {competitor.rating && (
            <div className="flex items-center gap-1 text-amber-400">
              <span>★</span>
              <span className="font-medium">{competitor.rating.toFixed(1)}</span>
              {competitor.review_count && (
                <span className="text-white/30 text-xs">({competitor.review_count})</span>
              )}
            </div>
          )}
          {hasDetails && (
            <span className="text-white/30 text-sm">{expanded ? "▲" : "▼"}</span>
          )}
        </div>
      </div>

      {expanded && hasDetails && (
        <div className="mt-3 pt-3 border-t border-white/5">
          {competitor.strengths && competitor.strengths.length > 0 && (
            <div className="mb-2">
              <p className="text-white/40 text-xs mb-1">Strengths</p>
              <div className="flex flex-wrap gap-2">
                {competitor.strengths.map((s, idx) => (
                  <span
                    key={idx}
                    className="text-xs bg-emerald-500/20 text-emerald-400 px-2 py-1 rounded"
                  >
                    {s}
                  </span>
                ))}
              </div>
            </div>
          )}
          {competitor.weaknesses && competitor.weaknesses.length > 0 && (
            <div>
              <p className="text-white/40 text-xs mb-1">Weaknesses</p>
              <div className="flex flex-wrap gap-2">
                {competitor.weaknesses.map((w, idx) => (
                  <span
                    key={idx}
                    className="text-xs bg-red-500/20 text-red-400 px-2 py-1 rounded"
                  >
                    {w}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ConversationCard({
  toolId,
  title,
  createdAt,
}: {
  toolId: string;
  title: string | null;
  createdAt: string;
}) {
  const toolNames: Record<string, string> = {
    location_scout: "Location Scout",
    market_validator: "Market Validator",
    competitor_analyzer: "Competitor Analyzer",
    social_media_coach: "Social Media Coach",
    review_responder: "Review Responder",
  };

  const date = new Date(createdAt);
  const formattedDate = date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });

  return (
    <div className="flex items-center justify-between py-3 border-b border-white/5 last:border-0">
      <div>
        <p className="text-white/50 text-sm">{toolNames[toolId] || toolId}</p>
        <p className="text-white font-medium truncate max-w-sm">
          {title || "New conversation"}
        </p>
      </div>
      <p className="text-white/30 text-sm">{formattedDate}</p>
    </div>
  );
}

function RecommendationItem({ text }: { text: string }) {
  const [done, setDone] = useState(false);

  return (
    <li className={`flex items-start gap-3 ${done ? "opacity-50" : ""}`}>
      <button
        onClick={() => setDone(!done)}
        className={`w-5 h-5 rounded border flex-shrink-0 flex items-center justify-center mt-0.5 transition-colors ${
          done
            ? "bg-emerald-500 border-emerald-500"
            : "border-white/20 hover:border-white/40"
        }`}
      >
        {done && (
          <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
          </svg>
        )}
      </button>
      <span className={`text-white/70 ${done ? "line-through" : ""}`}>{text}</span>
    </li>
  );
}

function getViabilityColor(score: number): "green" | "yellow" | "red" {
  if (score >= 70) return "green";
  if (score >= 40) return "yellow";
  return "red";
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadDashboard() {
      try {
        const sessionId = getSessionId();
        const dashboardData = await getDashboard(sessionId, user?.id);
        setData(dashboardData);
      } catch (err) {
        setError("Failed to load dashboard");
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadDashboard();
  }, [user]);

  return (
    <div className="min-h-screen bg-[#0a0a0a] relative overflow-hidden">
      {/* Grid pattern overlay */}
      <div className="fixed inset-0 grid-pattern pointer-events-none" />

      {/* Header */}
      <header className="dark-header fixed top-0 left-0 right-0 z-50 px-6 py-4">
        <div className="mx-auto max-w-6xl flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/" className="text-xl font-bold text-white hover:text-white/80 transition-colors tracking-tight">
              PHOW
            </Link>
            <span className="hidden sm:inline-flex items-center px-2 py-0.5 rounded bg-white/10 text-[10px] font-mono text-white/60 uppercase tracking-wider">
              Dashboard
            </span>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/community"
              className="px-4 py-2 text-white/70 hover:text-white text-sm font-medium transition-colors"
            >
              Community
            </Link>
            <Link
              href="/business-setup"
              className="px-4 py-2 text-white/70 hover:text-white text-sm font-medium transition-colors"
            >
              My Business
            </Link>
            <Link
              href="/app"
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white text-black text-sm font-medium hover:bg-white/90 transition-all"
            >
              New Analysis
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative z-10 pt-24 pb-12 px-6">
        <div className="max-w-6xl mx-auto">
          {loading ? (
            <div className="flex items-center justify-center min-h-[60vh]">
              <div className="text-white/50">Loading dashboard...</div>
            </div>
          ) : error ? (
            <div className="flex items-center justify-center min-h-[60vh]">
              <div className="text-red-400">{error}</div>
            </div>
          ) : !data?.has_profile ? (
            <div className="flex flex-col items-center justify-center min-h-[60vh] text-center animate-fade-in-up">
              <h1 className="text-3xl font-bold text-white mb-4">Welcome to <span className="text-accent-blue">PHOW</span></h1>
              <p className="text-white/50 mb-8 max-w-md">
                Set up your business profile to start getting insights about your market,
                competitors, and location.
              </p>
              <Link
                href="/business-setup"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-white text-black font-semibold hover:bg-white/90 transition-all"
              >
                Set Up Business Profile
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </Link>
            </div>
          ) : (
            <>
              {/* Business Header */}
              <div className="mb-8 animate-fade-in-up">
                <h1 className="text-3xl font-bold text-white">
                  {data.business_profile?.business_name || "Your Business"}
                </h1>
                <p className="text-white/50 mt-1">
                  {data.business_profile?.business_type}
                  {data.business_profile?.location_address &&
                    ` • ${data.business_profile.location_address}`}
                </p>
              </div>

              {/* Score Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                <ScoreCard
                  label="Viability Score"
                  value={data.market_analysis?.viability_score ?? "—"}
                  subtext={data.market_analysis ? "out of 100" : "Run Market Validator"}
                  color={
                    data.market_analysis
                      ? getViabilityColor(data.market_analysis.viability_score)
                      : undefined
                  }
                />
                <ScoreCard
                  label="Competitors Tracked"
                  value={data.tracked_competitors.length}
                  subtext={data.tracked_competitors.length > 0 ? "in your area" : "Run Competitor Analyzer"}
                  color="blue"
                />
                <ScoreCard
                  label="Competition Level"
                  value={data.competitor_analysis?.overall_competition_level ?? "—"}
                  subtext={data.competitor_analysis ? "based on analysis" : "Run Competitor Analyzer"}
                />
              </div>

              {/* Quick Insights */}
              {(data.market_analysis?.risk_factors?.length || data.market_analysis?.opportunities?.length) && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
                  {data.market_analysis?.risk_factors && data.market_analysis.risk_factors.length > 0 && (
                    <div className="dark-card p-6 border-l-4 border-red-500">
                      <h3 className="text-red-400 font-semibold mb-3 flex items-center gap-2">
                        <span>⚠️</span> Top Risks
                      </h3>
                      <ul className="space-y-2">
                        {data.market_analysis.risk_factors.slice(0, 3).map((risk, idx) => (
                          <li key={idx} className="flex items-start gap-2 text-white/70 text-sm">
                            <span className="text-red-400 mt-1">•</span>
                            <span>{risk}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {data.market_analysis?.opportunities && data.market_analysis.opportunities.length > 0 && (
                    <div className="dark-card p-6 border-l-4 border-emerald-500">
                      <h3 className="text-emerald-400 font-semibold mb-3 flex items-center gap-2">
                        <span>✨</span> Top Opportunities
                      </h3>
                      <ul className="space-y-2">
                        {data.market_analysis.opportunities.slice(0, 3).map((opp, idx) => (
                          <li key={idx} className="flex items-start gap-2 text-white/70 text-sm">
                            <span className="text-emerald-400 mt-1">•</span>
                            <span>{opp}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Demographics Section */}
              {data.market_analysis?.demographics && Object.keys(data.market_analysis.demographics).length > 0 && (
                <div className="dark-card p-6 mb-6">
                  <h2 className="text-xl font-semibold text-white mb-4">Market Demographics</h2>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {Object.entries(data.market_analysis.demographics).map(([key, value]) => (
                      <div key={key} className="bg-white/5 rounded-lg p-4">
                        <p className="text-white/40 text-sm mb-2 capitalize">
                          {key.replace(/_/g, " ")}
                        </p>
                        <p className="text-white font-medium">{String(value)}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Two Column Layout */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Competitors */}
                <div className="dark-card p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-semibold text-white">Top Competitors</h2>
                    <Link
                      href="/app?tool=competitor_analyzer"
                      className="text-blue-400 text-sm hover:underline"
                    >
                      Analyze More
                    </Link>
                  </div>
                  {data.tracked_competitors.length > 0 ? (
                    <div>
                      {data.tracked_competitors.slice(0, 5).map((competitor) => (
                        <CompetitorCard key={competitor.id} competitor={competitor} />
                      ))}
                      {data.tracked_competitors.length > 5 && (
                        <p className="text-white/30 text-sm mt-3 text-center">
                          +{data.tracked_competitors.length - 5} more competitors
                        </p>
                      )}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <p className="text-white/40 mb-4">No competitors tracked yet</p>
                      <Link
                        href="/app?tool=competitor_analyzer"
                        className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 text-white text-sm hover:bg-white/10 transition-all"
                      >
                        Find Competitors
                      </Link>
                    </div>
                  )}
                </div>

                {/* Recent Activity */}
                <div className="dark-card p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-semibold text-white">Recent Activity</h2>
                  </div>
                  {data.recent_conversations.length > 0 ? (
                    <div>
                      {data.recent_conversations.slice(0, 5).map((conversation) => (
                        <ConversationCard
                          key={conversation.id}
                          toolId={conversation.tool_id}
                          title={conversation.title}
                          createdAt={conversation.created_at}
                        />
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <p className="text-white/40 mb-4">No analyses yet</p>
                      <Link
                        href="/app"
                        className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 text-white text-sm hover:bg-white/10 transition-all"
                      >
                        Start Your First Analysis
                      </Link>
                    </div>
                  )}
                </div>
              </div>

              {/* Market Gaps */}
              {data.competitor_analysis?.market_gaps && Object.keys(data.competitor_analysis.market_gaps).length > 0 && (
                <div className="dark-card p-6 mt-6">
                  <h2 className="text-xl font-semibold text-white mb-2">Your Competitive Advantages</h2>
                  <p className="text-white/40 text-sm mb-4">
                    Gaps in the market where you can differentiate
                  </p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {Object.entries(data.competitor_analysis.market_gaps).map(([key, value]) => (
                      <div key={key} className="bg-white/5 rounded-lg p-4 border-l-2 border-blue-500">
                        <p className="text-blue-400 text-sm font-medium capitalize mb-1">
                          {key.replace(/_/g, " ")}
                        </p>
                        <p className="text-white/70 text-sm">{String(value)}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Differentiation Suggestions */}
              {data.competitor_analysis?.differentiation_suggestions &&
                data.competitor_analysis.differentiation_suggestions.length > 0 && (
                  <div className="dark-card p-6 mt-6">
                    <h2 className="text-xl font-semibold text-white mb-4">
                      Differentiation Strategies
                    </h2>
                    <ul className="space-y-2">
                      {data.competitor_analysis.differentiation_suggestions.map((sug, idx) => (
                        <li key={idx} className="flex items-start gap-3">
                          <span className="text-blue-400 mt-1">→</span>
                          <span className="text-white/70">{sug}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

              {/* Recommendations */}
              {data.market_analysis?.recommendations &&
                data.market_analysis.recommendations.length > 0 && (
                  <div className="dark-card p-6 mt-6">
                    <h2 className="text-xl font-semibold text-white mb-4">Action Items</h2>
                    <ul className="space-y-3">
                      {data.market_analysis.recommendations.map((rec, idx) => (
                        <RecommendationItem key={idx} text={rec} />
                      ))}
                    </ul>
                  </div>
                )}

              {/* Quick Actions */}
              <div className="flex flex-wrap gap-4 mt-8 justify-center">
                <Link
                  href="/app?tool=market_validator"
                  className="px-6 py-3 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 font-medium transition-all border border-emerald-500/20"
                >
                  Validate Market
                </Link>
                <Link
                  href="/app?tool=competitor_analyzer"
                  className="px-6 py-3 rounded-lg bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 font-medium transition-all border border-blue-500/20"
                >
                  Analyze Competitors
                </Link>
                <Link
                  href="/app?tool=location_scout"
                  className="px-6 py-3 rounded-lg bg-purple-500/10 hover:bg-purple-500/20 text-purple-400 font-medium transition-all border border-purple-500/20"
                >
                  Scout Location
                </Link>
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  );
}

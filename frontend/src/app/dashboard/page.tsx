"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import { getDashboard } from "@/lib/api";
import { getSessionId } from "@/lib/session";
import { DashboardData } from "@/types";

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
    blue: "text-sky-400",
  };

  return (
    <div className="glass-card p-6 text-center">
      <p className="text-white/60 text-sm mb-2">{label}</p>
      <p className={`text-3xl font-bold ${color ? colorClasses[color] : "text-white"}`}>
        {value}
      </p>
      {subtext && <p className="text-white/40 text-xs mt-1">{subtext}</p>}
    </div>
  );
}

function CompetitorCard({
  name,
  rating,
  address,
}: {
  name: string;
  rating: number | null;
  address: string | null;
}) {
  return (
    <div className="flex items-center justify-between py-3 border-b border-white/10 last:border-0">
      <div>
        <p className="text-white font-medium">{name}</p>
        {address && <p className="text-white/50 text-sm truncate max-w-xs">{address}</p>}
      </div>
      {rating && (
        <div className="flex items-center gap-1 text-amber-400">
          <span>★</span>
          <span className="font-medium">{rating.toFixed(1)}</span>
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
    <div className="flex items-center justify-between py-3 border-b border-white/10 last:border-0">
      <div>
        <p className="text-white/60 text-sm">{toolNames[toolId] || toolId}</p>
        <p className="text-white font-medium truncate max-w-sm">
          {title || "New conversation"}
        </p>
      </div>
      <p className="text-white/40 text-sm">{formattedDate}</p>
    </div>
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
    <div className="min-h-screen relative overflow-hidden">
      {/* Background */}
      <div
        className="absolute inset-0 z-0"
        style={{
          backgroundImage: `url('https://plus.unsplash.com/premium_photo-1664443577580-dd2674e9d359?q=80&w=2071&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D')`,
          backgroundSize: "cover",
          backgroundPosition: "center",
          backgroundRepeat: "no-repeat",
        }}
      />
      <div className="absolute inset-0 z-0 bg-gradient-to-b from-slate-900/40 via-transparent to-slate-900/60" />

      {/* Header */}
      <header className="glass-header fixed top-0 left-0 right-0 z-50 px-6 py-4">
        <div className="mx-auto max-w-6xl flex items-center justify-between">
          <Link
            href="/"
            className="text-left text-xl font-bold text-white hover:text-white/80 transition-colors"
          >
            <span className="text-2xl">PHOW</span>
          </Link>
          <div className="flex items-center gap-3">
            <Link
              href="/business-setup"
              className="px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white text-sm font-medium transition-all border border-white/20"
            >
              My Business
            </Link>
            <Link
              href="/"
              className="px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white text-sm font-medium transition-all border border-white/20"
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
              <div className="text-white/60">Loading dashboard...</div>
            </div>
          ) : error ? (
            <div className="flex items-center justify-center min-h-[60vh]">
              <div className="text-red-400">{error}</div>
            </div>
          ) : !data?.has_profile ? (
            <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
              <h1 className="text-3xl font-bold text-white mb-4">Welcome to PHOW</h1>
              <p className="text-white/60 mb-8 max-w-md">
                Set up your business profile to start getting insights about your market,
                competitors, and location.
              </p>
              <Link href="/business-setup" className="btn-primary">
                Set Up Business Profile
              </Link>
            </div>
          ) : (
            <>
              {/* Business Header */}
              <div className="mb-8">
                <h1 className="text-3xl font-bold text-white">
                  {data.business_profile?.business_name || "Your Business"}
                </h1>
                <p className="text-white/60 mt-1">
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

              {/* Two Column Layout */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Competitors */}
                <div className="glass-card p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-semibold text-white">Top Competitors</h2>
                    <Link
                      href="/?tool=competitor_analyzer"
                      className="text-sky-400 text-sm hover:underline"
                    >
                      Analyze More
                    </Link>
                  </div>
                  {data.tracked_competitors.length > 0 ? (
                    <div>
                      {data.tracked_competitors.slice(0, 5).map((competitor) => (
                        <CompetitorCard
                          key={competitor.id}
                          name={competitor.name}
                          rating={competitor.rating}
                          address={competitor.address}
                        />
                      ))}
                      {data.tracked_competitors.length > 5 && (
                        <p className="text-white/40 text-sm mt-3 text-center">
                          +{data.tracked_competitors.length - 5} more competitors
                        </p>
                      )}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <p className="text-white/50 mb-4">No competitors tracked yet</p>
                      <Link href="/?tool=competitor_analyzer" className="btn-primary text-sm">
                        Find Competitors
                      </Link>
                    </div>
                  )}
                </div>

                {/* Recent Activity */}
                <div className="glass-card p-6">
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
                      <p className="text-white/50 mb-4">No analyses yet</p>
                      <Link href="/" className="btn-primary text-sm">
                        Start Your First Analysis
                      </Link>
                    </div>
                  )}
                </div>
              </div>

              {/* Recommendations */}
              {data.market_analysis?.recommendations &&
                data.market_analysis.recommendations.length > 0 && (
                  <div className="glass-card p-6 mt-6">
                    <h2 className="text-xl font-semibold text-white mb-4">Recommendations</h2>
                    <ul className="space-y-2">
                      {data.market_analysis.recommendations.map((rec, idx) => (
                        <li key={idx} className="flex items-start gap-3">
                          <span className="text-emerald-400 mt-1">•</span>
                          <span className="text-white/80">{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

              {/* Quick Actions */}
              <div className="flex flex-wrap gap-4 mt-8 justify-center">
                <Link
                  href="/?tool=market_validator"
                  className="px-6 py-3 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 font-medium transition-all border border-emerald-500/30"
                >
                  Validate Market
                </Link>
                <Link
                  href="/?tool=competitor_analyzer"
                  className="px-6 py-3 rounded-lg bg-sky-500/20 hover:bg-sky-500/30 text-sky-400 font-medium transition-all border border-sky-500/30"
                >
                  Analyze Competitors
                </Link>
                <Link
                  href="/?tool=location_scout"
                  className="px-6 py-3 rounded-lg bg-purple-500/20 hover:bg-purple-500/30 text-purple-400 font-medium transition-all border border-purple-500/30"
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

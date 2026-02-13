"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import { getSessionId } from "@/lib/session";
import {
  fetchReviewAnalyticsSummary,
  fetchReviewAnalyticsTrends,
  fetchReviewAnalyticsThemes,
  fetchReviewAnalyticsPlatforms,
} from "@/lib/api";
import { PlatformMetric, ReviewAnalyticsSummary, ReviewTrendPoint, ThemeMetric } from "@/types";

export default function ReputationAnalyticsPage() {
  const { user } = useAuth();
  const [summary, setSummary] = useState<ReviewAnalyticsSummary | null>(null);
  const [trends, setTrends] = useState<ReviewTrendPoint[]>([]);
  const [themes, setThemes] = useState<ThemeMetric[]>([]);
  const [platforms, setPlatforms] = useState<PlatformMetric[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const sessionId = getSessionId();
        const [s, t, th, p] = await Promise.all([
          fetchReviewAnalyticsSummary(sessionId, user?.id),
          fetchReviewAnalyticsTrends(sessionId, user?.id),
          fetchReviewAnalyticsThemes(sessionId, user?.id),
          fetchReviewAnalyticsPlatforms(sessionId, user?.id),
        ]);
        setSummary(s);
        setTrends(t);
        setThemes(th);
        setPlatforms(p);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load analytics");
      }
    }
    void load();
  }, [user?.id]);

  return (
    <main className="relative z-10 pt-24 pb-10 px-6">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-white">Reputation Analytics</h1>
          <Link href="/reputation" className="text-blue-400 text-sm hover:underline">Back to Inbox</Link>
        </div>
        {error && <p className="text-red-400 text-sm mb-4">{error}</p>}

        <div className="grid md:grid-cols-4 gap-4 mb-6">
          <div className="dark-card p-4"><p className="text-white/60 text-xs">Total Reviews</p><p className="text-white text-2xl font-bold">{summary?.total_reviews ?? "-"}</p></div>
          <div className="dark-card p-4"><p className="text-white/60 text-xs">Avg Rating</p><p className="text-white text-2xl font-bold">{summary?.avg_rating ?? "-"}</p></div>
          <div className="dark-card p-4"><p className="text-white/60 text-xs">Response Rate</p><p className="text-white text-2xl font-bold">{summary?.response_rate ?? "-"}%</p></div>
          <div className="dark-card p-4"><p className="text-white/60 text-xs">Window</p><p className="text-white text-2xl font-bold">{summary?.window_days ?? "-"}d</p></div>
        </div>

        <div className="grid lg:grid-cols-2 gap-6">
          <section className="dark-card p-4">
            <h2 className="text-white font-semibold mb-3">Daily Trends</h2>
            <div className="space-y-2 text-sm">
              {trends.slice(0, 10).map((point) => (
                <div key={point.date} className="flex justify-between text-white/80 border-b border-white/10 pb-1">
                  <span>{point.date}</span>
                  <span>{point.review_count} reviews · {point.avg_rating}★</span>
                </div>
              ))}
            </div>
          </section>

          <section className="dark-card p-4">
            <h2 className="text-white font-semibold mb-3">Top Themes</h2>
            <div className="space-y-2 text-sm">
              {themes.slice(0, 10).map((theme) => (
                <div key={theme.theme} className="flex justify-between text-white/80 border-b border-white/10 pb-1">
                  <span className="capitalize">{theme.theme}</span>
                  <span>{theme.count}</span>
                </div>
              ))}
            </div>
          </section>

          <section className="dark-card p-4 lg:col-span-2">
            <h2 className="text-white font-semibold mb-3">Platform Performance</h2>
            <div className="grid md:grid-cols-3 gap-3">
              {platforms.map((platform) => (
                <div key={platform.source} className="border border-white/10 rounded p-3">
                  <p className="text-white font-medium capitalize">{platform.source}</p>
                  <p className="text-white/70 text-sm">{platform.review_count} reviews</p>
                  <p className="text-white/70 text-sm">Avg {platform.avg_rating}★</p>
                  <p className="text-white/70 text-sm">Response {platform.response_rate}%</p>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}

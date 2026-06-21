"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ShieldCheck, Star } from "lucide-react";
import { fetchAnalytics } from "@/lib/reviews-api";
import type { ReviewAnalytics } from "@/lib/reviews-api";

export function ReputationWidget({ businessProfileId }: { businessProfileId: string }) {
  const [analytics, setAnalytics] = useState<ReviewAnalytics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    fetchAnalytics(businessProfileId)
      .then((a) => !cancelled && setAnalytics(a))
      .catch(() => {})
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [businessProfileId]);

  const needs = analytics?.needs_response ?? 0;

  return (
    <div className="dark-card p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-blue-400" />
          <h2 className="text-lg font-semibold text-white">Reputation</h2>
          {needs > 0 && (
            <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300">
              {needs} to reply
            </span>
          )}
        </div>
        <Link
          href={`/reviews?bid=${businessProfileId}`}
          className="text-blue-400 text-sm hover:underline"
        >
          Open Hub
        </Link>
      </div>

      {loading ? (
        <div className="h-12 rounded-lg bg-white/5 animate-pulse" />
      ) : !analytics || analytics.total_reviews === 0 ? (
        <p className="text-sm text-white/40">
          Connect Google Business Profile to monitor and reply to your reviews from one place.
        </p>
      ) : (
        <div className="flex items-center gap-8">
          <Stat label="Reviews" value={String(analytics.total_reviews)} />
          <Stat
            label="Avg rating"
            value={analytics.average_rating != null ? analytics.average_rating.toFixed(1) : "—"}
            star
          />
          <Stat label="Response rate" value={`${Math.round(analytics.response_rate * 100)}%`} />
        </div>
      )}
    </div>
  );
}

function Stat({ label, value, star }: { label: string; value: string; star?: boolean }) {
  return (
    <div>
      <div className="text-xl font-bold text-white flex items-center gap-1">
        {star && <Star className="w-4 h-4 fill-amber-400 text-amber-400" />}
        {value}
      </div>
      <div className="text-[11px] uppercase tracking-wide text-white/40">{label}</div>
    </div>
  );
}

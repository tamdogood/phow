"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Radar } from "lucide-react";
import { fetchRadarFeed, severityStyle, relativeTime } from "@/lib/radar-api";
import type { RadarAlert } from "@/lib/radar-api";

export function RadarWidget({ businessProfileId }: { businessProfileId: string }) {
  const [alerts, setAlerts] = useState<RadarAlert[]>([]);
  const [unread, setUnread] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    fetchRadarFeed(businessProfileId, undefined, 5)
      .then((feed) => {
        if (cancelled) return;
        setAlerts(feed.alerts ?? []);
        setUnread(feed.unread_count ?? 0);
      })
      .catch(() => {})
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [businessProfileId]);

  return (
    <div className="dark-card p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Radar className="w-5 h-5 text-blue-400" />
          <h2 className="text-lg font-semibold text-white">Business Radar</h2>
          {unread > 0 && (
            <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-300">
              {unread} new
            </span>
          )}
        </div>
        <Link
          href={`/radar?bid=${businessProfileId}`}
          className="text-blue-400 text-sm hover:underline"
        >
          View all
        </Link>
      </div>

      {loading ? (
        <div className="space-y-2">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-12 rounded-lg bg-white/5 animate-pulse" />
          ))}
        </div>
      ) : alerts.length === 0 ? (
        <p className="text-sm text-white/40">
          No alerts yet. Open the Radar to run your first scan and start monitoring news that could
          affect your business.
        </p>
      ) : (
        <div>
          {alerts.map((a) => {
            const s = severityStyle(a.severity);
            return (
              <a
                key={a.id}
                href={a.url || `/radar?bid=${businessProfileId}`}
                target={a.url ? "_blank" : undefined}
                rel="noreferrer"
                className="block py-3 border-b border-white/5 last:border-0 hover:bg-white/[0.03] -mx-2 px-2 rounded"
              >
                <div className="flex items-center gap-2 mb-0.5">
                  <span className={`inline-block w-1.5 h-1.5 rounded-full ${s.dot}`} />
                  <span className="text-[10px] uppercase tracking-wide text-white/40">
                    {a.category}
                  </span>
                  <span className="text-[10px] text-white/30 ml-auto">
                    {relativeTime(a.published_at || a.created_at)}
                  </span>
                </div>
                <p className="text-sm text-white/90 truncate">{a.title}</p>
                {a.why_it_matters && (
                  <p className="text-xs text-white/50 truncate">{a.why_it_matters}</p>
                )}
              </a>
            );
          })}
        </div>
      )}
    </div>
  );
}

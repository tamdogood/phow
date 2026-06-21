"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import {
  Star,
  RefreshCw,
  Sparkles,
  Send,
  Plus,
  ShieldCheck,
  Loader2,
  TrendingUp,
  TrendingDown,
  Trash2,
} from "lucide-react";
import { AppHeader } from "@/components/AppHeader";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  fetchConnections,
  startGoogleConnect,
  deleteConnection,
  syncReviews,
  fetchInbox,
  fetchAnalytics,
  generateDrafts,
  publishReply,
  addManualReview,
  sentimentStyle,
  statusStyle,
  relativeTime,
  REVIEWS_MOCK,
} from "@/lib/reviews-api";
import type {
  Review,
  ReviewConnection,
  ReviewAnalytics,
  ReviewDraft,
  InboxFilter,
} from "@/lib/reviews-api";

export default function ReviewsPage() {
  return (
    <Suspense fallback={<Shell><div className="py-32 text-center text-white/40">Loading…</div></Shell>}>
      <ReviewsInner />
    </Suspense>
  );
}

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-[#0a0a0a] relative overflow-hidden">
      <div className="fixed inset-0 grid-pattern pointer-events-none" />
      <AppHeader />
      <main className="relative z-10 pt-24 pb-16 px-6">
        <div className="max-w-5xl mx-auto">{children}</div>
      </main>
    </div>
  );
}

function ReviewsInner() {
  const params = useSearchParams();
  const bid = params.get("bid") || (REVIEWS_MOCK ? "demo" : "");

  const [connections, setConnections] = useState<ReviewConnection[]>([]);
  const [analytics, setAnalytics] = useState<ReviewAnalytics | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [filter, setFilter] = useState<InboxFilter>("all");
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  const googleConn = connections.find((c) => c.platform === "google" && c.status === "connected");

  const load = useCallback(async () => {
    if (!bid) return;
    try {
      const [conns, stats, inbox] = await Promise.all([
        fetchConnections(bid),
        fetchAnalytics(bid),
        fetchInbox(bid, filter),
      ]);
      setConnections(conns);
      setAnalytics(stats);
      setReviews(inbox);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to load reviews");
    } finally {
      setLoading(false);
    }
  }, [bid, filter]);

  useEffect(() => {
    void load();
  }, [load]);

  // Toast on OAuth redirect outcome
  useEffect(() => {
    if (params.get("connected") === "google") toast.success("Google Business Profile connected");
    const err = params.get("error");
    if (err) toast.error(`Connection failed: ${err}`);
  }, [params]);

  async function handleConnect() {
    try {
      const { authorization_url } = await startGoogleConnect(bid);
      window.location.href = authorization_url;
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not start Google connection");
    }
  }

  async function handleSync() {
    setSyncing(true);
    try {
      const res = await syncReviews(bid);
      if (res.status === "ok") toast.success(`Synced ${res.synced} reviews`);
      else if (res.status === "not_connected") toast.error("Connect Google first");
      else toast.error("Sync failed — check the connection");
      await load();
    } finally {
      setSyncing(false);
    }
  }

  async function handleDisconnect(id: string) {
    await deleteConnection(id);
    toast.success("Disconnected");
    await load();
  }

  if (!bid) {
    return (
      <Shell>
        <EmptyState
          title="Open the Reputation Hub from your dashboard"
          body="The Hub needs a business profile. Head to your dashboard and open Reputation from there."
          action={<Link href="/dashboard"><Button>Go to dashboard</Button></Link>}
        />
      </Shell>
    );
  }

  return (
    <Shell>
      {/* Header */}
      <div className="flex flex-wrap items-end justify-between gap-4 mb-8">
        <div>
          <div className="flex items-center gap-2 text-white/50 text-sm mb-1">
            <ShieldCheck className="h-4 w-4 text-blue-400" /> Reputation Hub
            {REVIEWS_MOCK && (
              <span className="ml-1 rounded-full border border-amber-500/30 bg-amber-500/15 px-2 py-0.5 text-[10px] font-medium text-amber-300">
                Demo data
              </span>
            )}
          </div>
          <h1 className="text-3xl font-bold text-white">Protect your reputation</h1>
          <p className="text-white/50 mt-1">
            Monitor and reply to your Google reviews from one place.
          </p>
        </div>
        {googleConn && (
          <Button onClick={handleSync} disabled={syncing} variant="secondary">
            <RefreshCw className={`h-4 w-4 ${syncing ? "animate-spin" : ""}`} />
            {syncing ? "Syncing…" : "Sync now"}
          </Button>
        )}
      </div>

      {loading ? (
        <div className="space-y-4">
          <Skeleton className="h-28 w-full rounded-2xl" />
          <Skeleton className="h-40 w-full rounded-2xl" />
        </div>
      ) : (
        <>
          <ConnectionPanel
            conn={googleConn}
            onConnect={handleConnect}
            onDisconnect={handleDisconnect}
          />

          {analytics && analytics.total_reviews > 0 && <Overview analytics={analytics} />}

          <ManualAdd bid={bid} onAdded={load} />

          {/* Inbox */}
          <div className="mt-8">
            <Tabs value={filter} onValueChange={(v) => setFilter(v as InboxFilter)}>
              <TabsList>
                <TabsTrigger value="all">All</TabsTrigger>
                <TabsTrigger value="unreplied">Unreplied</TabsTrigger>
                <TabsTrigger value="negative">Negative</TabsTrigger>
              </TabsList>
            </Tabs>

            <div className="mt-4 space-y-4">
              {reviews.length === 0 ? (
                <EmptyState
                  title="No reviews yet"
                  body={
                    googleConn
                      ? "Hit “Sync now” to pull your latest Google reviews, or add one manually to try the workflow."
                      : "Connect Google to import your reviews, or add one manually to try the workflow."
                  }
                />
              ) : (
                reviews.map((r) => <ReviewCard key={r.id} review={r} onPublished={load} />)
              )}
            </div>
          </div>
        </>
      )}
    </Shell>
  );
}

function ConnectionPanel({
  conn,
  onConnect,
  onDisconnect,
}: {
  conn?: ReviewConnection;
  onConnect: () => void;
  onDisconnect: (id: string) => void;
}) {
  if (conn) {
    return (
      <div className="dark-card p-5 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="grid h-9 w-9 place-items-center rounded-lg bg-emerald-500/15 text-emerald-300">
            <ShieldCheck className="h-5 w-5" />
          </span>
          <div>
            <div className="text-white font-medium">
              {conn.location_label || "Google Business Profile"}
            </div>
            <div className="text-xs text-white/40">
              Connected · last sync {conn.last_sync_at ? relativeTime(conn.last_sync_at) : "—"}
              {conn.last_sync_status === "error" && (
                <span className="text-red-400"> · sync error</span>
              )}
            </div>
          </div>
        </div>
        <Button variant="ghost" size="sm" onClick={() => onDisconnect(conn.id)}>
          <Trash2 className="h-4 w-4" /> Disconnect
        </Button>
      </div>
    );
  }
  return (
    <div className="dark-card p-6 flex flex-wrap items-center justify-between gap-4">
      <div>
        <div className="text-white font-medium">Connect Google Business Profile</div>
        <p className="text-sm text-white/50 mt-1 max-w-md">
          Authorize PHOW to read your reviews and post replies on your behalf.
        </p>
      </div>
      <Button onClick={onConnect}>
        <Plus className="h-4 w-4" /> Connect Google
      </Button>
    </div>
  );
}

function Overview({ analytics }: { analytics: ReviewAnalytics }) {
  const { recent_30d, prior_30d } = analytics.rating_trend;
  const trendUp = recent_30d != null && prior_30d != null && recent_30d >= prior_30d;
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
      <Stat label="Reviews" value={String(analytics.total_reviews)} />
      <Stat
        label="Avg rating"
        value={analytics.average_rating != null ? analytics.average_rating.toFixed(1) : "—"}
        sub={
          recent_30d != null && prior_30d != null ? (
            <span className={`inline-flex items-center gap-1 ${trendUp ? "text-emerald-400" : "text-red-400"}`}>
              {trendUp ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
              {recent_30d} vs {prior_30d} (30d)
            </span>
          ) : undefined
        }
      />
      <Stat label="Needs reply" value={String(analytics.needs_response)} />
      <Stat label="Response rate" value={`${Math.round(analytics.response_rate * 100)}%`} />
      {analytics.top_themes.length > 0 && (
        <div className="dark-card p-4 col-span-2 md:col-span-4">
          <div className="text-xs uppercase tracking-wide text-white/40 mb-2">Top themes</div>
          <div className="flex flex-wrap gap-2">
            {analytics.top_themes.map((t) => (
              <Badge key={t.theme} variant="outline" className="border-white/15 text-white/70">
                {t.theme} · {t.count}
              </Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value, sub }: { label: string; value: string; sub?: React.ReactNode }) {
  return (
    <div className="dark-card p-4">
      <div className="text-xs uppercase tracking-wide text-white/40">{label}</div>
      <div className="text-2xl font-bold text-white mt-1">{value}</div>
      {sub && <div className="text-xs mt-1">{sub}</div>}
    </div>
  );
}

function StarRating({ rating }: { rating?: number | null }) {
  return (
    <div className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((i) => (
        <Star
          key={i}
          className={`h-4 w-4 ${
            rating && i <= rating ? "fill-amber-400 text-amber-400" : "text-white/20"
          }`}
        />
      ))}
    </div>
  );
}

function ReviewCard({ review, onPublished }: { review: Review; onPublished: () => void }) {
  const [drafts, setDrafts] = useState<ReviewDraft[]>([]);
  const [reply, setReply] = useState(review.response_text || "");
  const [drafting, setDrafting] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [composing, setComposing] = useState(false);

  const sent = sentimentStyle(review.sentiment);
  const status = statusStyle(review.response_status);
  const responded = review.response_status === "responded";

  async function handleDraft() {
    setDrafting(true);
    try {
      const d = await generateDrafts(review.id);
      setDrafts(d);
      setReply(d[0]?.text || "");
      setComposing(true);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not generate drafts");
    } finally {
      setDrafting(false);
    }
  }

  async function handlePublish() {
    if (!reply.trim()) return;
    setPublishing(true);
    try {
      await publishReply(review.id, reply.trim());
      toast.success(review.source === "google" ? "Reply published to Google" : "Reply saved");
      setComposing(false);
      onPublished();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to publish");
    } finally {
      setPublishing(false);
    }
  }

  return (
    <div className="dark-card p-5">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <StarRating rating={review.rating} />
          <div>
            <span className="text-white font-medium">{review.author_name || "Anonymous"}</span>
            <span className="text-white/30 text-xs ml-2">
              {review.source === "manual" ? "Manual" : "Google"} ·{" "}
              {relativeTime(review.review_created_at)}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className={sent.badge}>{sent.label}</Badge>
          <Badge variant="outline" className={status.badge}>{status.label}</Badge>
        </div>
      </div>

      {review.review_text && <p className="text-white/80 mt-3 leading-relaxed">{review.review_text}</p>}

      {review.themes && review.themes.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-3">
          {review.themes.map((t) => (
            <span key={t} className="text-[11px] px-2 py-0.5 rounded-full bg-white/[0.05] text-white/50">
              {t}
            </span>
          ))}
        </div>
      )}

      {/* Response area */}
      {responded && !composing ? (
        <div className="mt-4 rounded-lg border border-white/[0.06] bg-white/[0.02] p-3">
          <div className="text-xs text-emerald-300/80 mb-1">Your reply</div>
          <p className="text-sm text-white/70">{review.response_text}</p>
          <button
            className="text-xs text-white/40 hover:text-white/70 mt-2"
            onClick={() => setComposing(true)}
          >
            Edit reply
          </button>
        </div>
      ) : composing ? (
        <div className="mt-4 space-y-3">
          {drafts.length > 1 && (
            <div className="flex flex-wrap gap-2">
              {drafts.map((d) => (
                <button
                  key={d.tone}
                  onClick={() => setReply(d.text)}
                  className="text-xs capitalize px-2.5 py-1 rounded-full border border-white/15 text-white/60 hover:text-white hover:border-white/30"
                >
                  {d.tone}
                </button>
              ))}
            </div>
          )}
          <textarea
            value={reply}
            onChange={(e) => setReply(e.target.value)}
            rows={4}
            className="w-full rounded-lg bg-white/[0.03] border border-white/10 p-3 text-sm text-white placeholder-white/30 focus:outline-none focus:border-white/25"
            placeholder="Write your reply…"
          />
          <div className="flex items-center gap-2">
            <Button size="sm" onClick={handlePublish} disabled={publishing || !reply.trim()}>
              {publishing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              {review.source === "google" ? "Publish to Google" : "Save reply"}
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setComposing(false)}>
              Cancel
            </Button>
          </div>
        </div>
      ) : (
        <div className="mt-4 flex items-center gap-2">
          <Button size="sm" variant="secondary" onClick={handleDraft} disabled={drafting}>
            {drafting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
            Draft AI replies
          </Button>
          <Button size="sm" variant="ghost" onClick={() => setComposing(true)}>
            Write manually
          </Button>
        </div>
      )}
    </div>
  );
}

function ManualAdd({ bid, onAdded }: { bid: string; onAdded: () => void }) {
  const [open, setOpen] = useState(false);
  const [author, setAuthor] = useState("");
  const [rating, setRating] = useState(5);
  const [text, setText] = useState("");
  const [saving, setSaving] = useState(false);

  async function submit() {
    if (!text.trim()) return;
    setSaving(true);
    try {
      await addManualReview({ business_profile_id: bid, review_text: text.trim(), author_name: author || undefined, rating });
      toast.success("Review added");
      setText("");
      setAuthor("");
      setOpen(false);
      onAdded();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to add review");
    } finally {
      setSaving(false);
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="mt-6 text-sm text-white/40 hover:text-white/70 inline-flex items-center gap-1.5"
      >
        <Plus className="h-3.5 w-3.5" /> Add a review manually
      </button>
    );
  }

  return (
    <div className="dark-card p-5 mt-6 space-y-3">
      <div className="flex items-center gap-3">
        <input
          value={author}
          onChange={(e) => setAuthor(e.target.value)}
          placeholder="Author (optional)"
          className="flex-1 rounded-lg bg-white/[0.03] border border-white/10 px-3 py-2 text-sm text-white placeholder-white/30 focus:outline-none focus:border-white/25"
        />
        <select
          value={rating}
          onChange={(e) => setRating(Number(e.target.value))}
          className="rounded-lg bg-white/[0.03] border border-white/10 px-3 py-2 text-sm text-white focus:outline-none"
        >
          {[5, 4, 3, 2, 1].map((r) => (
            <option key={r} value={r} className="bg-[#111]">{r} ★</option>
          ))}
        </select>
      </div>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={3}
        placeholder="Paste the review text…"
        className="w-full rounded-lg bg-white/[0.03] border border-white/10 p-3 text-sm text-white placeholder-white/30 focus:outline-none focus:border-white/25"
      />
      <div className="flex items-center gap-2">
        <Button size="sm" onClick={submit} disabled={saving || !text.trim()}>
          {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
          Add review
        </Button>
        <Button size="sm" variant="ghost" onClick={() => setOpen(false)}>Cancel</Button>
      </div>
    </div>
  );
}

function EmptyState({
  title,
  body,
  action,
}: {
  title: string;
  body: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="dark-card p-10 text-center">
      <div className="text-white font-medium">{title}</div>
      <p className="text-white/50 text-sm mt-1 max-w-md mx-auto">{body}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

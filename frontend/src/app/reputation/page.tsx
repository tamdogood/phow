"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import { getSessionId } from "@/lib/session";
import {
  fetchReviewInbox,
  fetchReviewDetail,
  generateReviewDrafts,
  publishReviewResponse,
  syncReviews,
} from "@/lib/api";
import { Review, ReviewResponseDraft } from "@/types";

export default function ReputationInboxPage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [selectedReview, setSelectedReview] = useState<Review | null>(null);
  const [drafts, setDrafts] = useState<ReviewResponseDraft[]>([]);
  const [publishingTone, setPublishingTone] = useState<string | null>(null);
  const [editedTexts, setEditedTexts] = useState<Record<string, string>>({});
  const [sourceFilter, setSourceFilter] = useState<"google" | "yelp" | "meta" | "">("");

  async function loadInbox() {
    setLoading(true);
    setError(null);
    try {
      const sessionId = getSessionId();
      const data = await fetchReviewInbox({
        sessionId,
        userId: user?.id,
        source: sourceFilter || undefined,
        limit: 50,
      });
      setReviews(data.items);
      if (data.items.length > 0 && !selectedReview) {
        await loadReview(data.items[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load inbox");
    } finally {
      setLoading(false);
    }
  }

  async function loadReview(reviewId: string) {
    try {
      const sessionId = getSessionId();
      const data = await fetchReviewDetail(reviewId, sessionId, user?.id);
      setSelectedReview(data.review);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load review");
    }
  }

  useEffect(() => {
    void loadInbox();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id, sourceFilter]);

  const actor = useMemo(() => ({ session_id: getSessionId(), user_id: user?.id }), [user?.id]);

  async function handleSync() {
    setSyncing(true);
    setError(null);
    try {
      await syncReviews(actor, sourceFilter || undefined);
      await loadInbox();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sync failed");
    } finally {
      setSyncing(false);
    }
  }

  async function handleGenerateDrafts() {
    if (!selectedReview) return;
    setError(null);
    try {
      const generated = await generateReviewDrafts(selectedReview.id, actor);
      setDrafts(generated);
      setEditedTexts(
        Object.fromEntries(generated.map((draft) => [draft.id, draft.edited_text || draft.draft_text]))
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Draft generation failed");
    }
  }

  async function handlePublish(draft: ReviewResponseDraft) {
    if (!selectedReview) return;
    setPublishingTone(draft.tone);
    setError(null);
    try {
      const text = editedTexts[draft.id] || draft.draft_text;
      await publishReviewResponse(
        selectedReview.id,
        actor,
        text,
        draft.tone,
        crypto.randomUUID()
      );
      await loadInbox();
      await loadReview(selectedReview.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Publish failed");
    } finally {
      setPublishingTone(null);
    }
  }

  return (
    <main className="relative z-10 pt-24 pb-10 px-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
          <div>
            <h1 className="text-3xl font-bold text-white">Reputation Inbox</h1>
            <p className="text-white/60 text-sm">Sync reviews, generate replies, and publish responses.</p>
          </div>
          <div className="flex items-center gap-2">
            <Link href="/reputation/connections" className="px-3 py-2 rounded-lg bg-white/10 text-white text-sm hover:bg-white/20">
              Connections
            </Link>
            <button
              onClick={handleSync}
              disabled={syncing}
              className="px-3 py-2 rounded-lg bg-blue-500/80 text-white text-sm hover:bg-blue-500 disabled:opacity-50"
            >
              {syncing ? "Syncing..." : "Sync Now"}
            </button>
          </div>
        </div>

        <div className="mb-4 flex items-center gap-2">
          <label className="text-white/70 text-sm">Source</label>
          <select
            className="bg-white/10 text-white rounded px-2 py-1 text-sm"
            value={sourceFilter}
            onChange={(e) => setSourceFilter(e.target.value as "google" | "yelp" | "meta" | "")}
          >
            <option value="">All</option>
            <option value="google">Google</option>
            <option value="yelp">Yelp</option>
            <option value="meta">Meta</option>
          </select>
        </div>

        {error && <p className="text-red-400 text-sm mb-4">{error}</p>}

        <div className="grid lg:grid-cols-2 gap-6">
          <section className="dark-card p-4 max-h-[70vh] overflow-y-auto">
            <h2 className="text-white font-semibold mb-3">Reviews</h2>
            {loading ? (
              <p className="text-white/50 text-sm">Loading...</p>
            ) : reviews.length === 0 ? (
              <p className="text-white/50 text-sm">No reviews yet. Connect sources and sync.</p>
            ) : (
              <div className="space-y-2">
                {reviews.map((review) => (
                  <button
                    key={review.id}
                    onClick={() => loadReview(review.id)}
                    className={`w-full text-left rounded-lg border px-3 py-2 transition ${
                      selectedReview?.id === review.id
                        ? "border-blue-400 bg-blue-500/10"
                        : "border-white/10 hover:border-white/30"
                    }`}
                  >
                    <div className="flex justify-between items-center">
                      <p className="text-white font-medium">{review.reviewer_name || "Anonymous"}</p>
                      <span className="text-amber-400 text-sm">{review.rating}★</span>
                    </div>
                    <p className="text-white/70 text-sm line-clamp-2">{review.content || "No text"}</p>
                    <p className="text-white/40 text-xs mt-1">{review.source} · {review.reply_status}</p>
                  </button>
                ))}
              </div>
            )}
          </section>

          <section className="dark-card p-4">
            <h2 className="text-white font-semibold mb-3">Reply Workflow</h2>
            {!selectedReview ? (
              <p className="text-white/50 text-sm">Select a review to start.</p>
            ) : (
              <div>
                <p className="text-white font-medium mb-1">{selectedReview.reviewer_name || "Anonymous"}</p>
                <p className="text-amber-400 text-sm mb-2">{selectedReview.rating}★</p>
                <p className="text-white/70 text-sm mb-4">{selectedReview.content || "No review body"}</p>

                <button
                  onClick={handleGenerateDrafts}
                  className="px-3 py-2 rounded bg-emerald-500/80 text-white text-sm hover:bg-emerald-500"
                >
                  Generate 3 Drafts
                </button>

                <div className="mt-4 space-y-4">
                  {drafts.map((draft) => (
                    <div key={draft.id} className="border border-white/10 rounded-lg p-3">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-white text-sm font-semibold capitalize">{draft.tone}</p>
                        <button
                          onClick={() => handlePublish(draft)}
                          disabled={publishingTone === draft.tone}
                          className="px-2 py-1 rounded bg-blue-500/80 text-white text-xs disabled:opacity-50"
                        >
                          {publishingTone === draft.tone ? "Publishing..." : "Publish"}
                        </button>
                      </div>
                      <textarea
                        value={editedTexts[draft.id] || draft.draft_text}
                        onChange={(e) => setEditedTexts((prev) => ({ ...prev, [draft.id]: e.target.value }))}
                        className="w-full min-h-24 bg-black/30 border border-white/15 rounded p-2 text-sm text-white"
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}

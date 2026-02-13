"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import { getSessionId } from "@/lib/session";
import { fetchReviewCompetitors } from "@/lib/api";
import { CompetitorComparison } from "@/types";

export default function ReputationCompetitorsPage() {
  const { user } = useAuth();
  const [items, setItems] = useState<CompetitorComparison[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchReviewCompetitors(getSessionId(), user?.id);
        setItems(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load competitors");
      }
    }
    void load();
  }, [user?.id]);

  return (
    <main className="relative z-10 pt-24 pb-10 px-6">
      <div className="max-w-5xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-white">Competitor Comparison</h1>
          <Link href="/dashboard" className="text-blue-400 text-sm hover:underline">Back to Dashboard</Link>
        </div>

        {error && <p className="text-red-400 text-sm mb-4">{error}</p>}

        {items.length === 0 ? (
          <div className="dark-card p-6 text-white/60">No tracked competitors yet.</div>
        ) : (
          <div className="grid md:grid-cols-2 gap-4">
            {items.map((item) => (
              <div key={item.id} className="dark-card p-4">
                <h2 className="text-white font-semibold mb-1">{item.name}</h2>
                <p className="text-white/60 text-sm mb-2">{item.address || "No address"}</p>
                <p className="text-white/80 text-sm">Rating: {item.rating ?? "-"}</p>
                <p className="text-white/80 text-sm">Reviews: {item.review_count ?? "-"}</p>
                <p className="text-white/80 text-sm">Price: {item.price_level ? "$".repeat(item.price_level) : "-"}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { AppHeader } from "@/components/AppHeader";
import { useAuth } from "@/contexts/AuthContext";
import { getSessionId } from "@/lib/session";
import { createFeasibilityReport } from "@/lib/feasibility-api";

const EXAMPLES = ["specialty coffee shop", "neighborhood pizzeria", "craft cocktail bar", "boba tea shop", "fast-casual taqueria", "brunch cafe"];

export default function FeasibilityIntakePage() {
  const router = useRouter();
  const { user } = useAuth();
  const [concept, setConcept] = useState("");
  const [address, setAddress] = useState("");
  const [seats, setSeats] = useState("");
  const [budget, setBudget] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!concept.trim() || !address.trim()) {
      setError("A concept and a location are required.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const report = await createFeasibilityReport({
        session_id: getSessionId(),
        user_id: user?.id,
        concept: concept.trim(),
        location_address: address.trim(),
        scale_seats: seats ? Number(seats) : undefined,
        startup_budget: budget ? Number(budget) : undefined,
      });
      router.push(`/report/${report.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start the study");
      setSubmitting(false);
    }
  }

  const inputCls =
    "w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white placeholder:text-white/30 focus:outline-none focus:border-white/30";

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      <AppHeader />
      <div className="pt-[72px] max-w-2xl mx-auto px-6 py-10">
        <Link href="/" className="text-white/40 hover:text-white text-sm">&larr; Home</Link>
        <h1 className="text-3xl font-bold mt-4 mb-2">Feasibility Study</h1>
        <p className="text-white/50 mb-8">
          The agency-grade analysis — demographics, competition, demand, financials and a clear go/no-go — for a food &amp; drink concept at a location. Ready in a few minutes.
        </p>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="text-sm text-white/70 block mb-2">What&apos;s the concept?</label>
            <input className={inputCls} value={concept} onChange={(e) => setConcept(e.target.value)} placeholder="e.g. specialty coffee shop" />
            <div className="flex flex-wrap gap-2 mt-2">
              {EXAMPLES.map((ex) => (
                <button key={ex} type="button" onClick={() => setConcept(ex)} className="text-xs px-2.5 py-1 rounded-full bg-white/5 border border-white/10 text-white/60 hover:text-white hover:border-white/30 transition-colors">
                  {ex}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="text-sm text-white/70 block mb-2">Where? (address or area)</label>
            <input className={inputCls} value={address} onChange={(e) => setAddress(e.target.value)} placeholder="e.g. 500 W 2nd St, Austin, TX" />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-white/70 block mb-2">Seats <span className="text-white/30">(optional)</span></label>
              <input className={inputCls} type="number" min={0} value={seats} onChange={(e) => setSeats(e.target.value)} placeholder="30" />
            </div>
            <div>
              <label className="text-sm text-white/70 block mb-2">Startup budget <span className="text-white/30">(optional)</span></label>
              <input className={inputCls} type="number" min={0} value={budget} onChange={(e) => setBudget(e.target.value)} placeholder="250000" />
            </div>
          </div>

          {error && <div className="bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-3 text-sm text-red-400">{error}</div>}

          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-3.5 rounded-lg transition-colors"
          >
            {submitting ? "Starting your study…" : "Generate feasibility study"}
          </button>
        </form>
      </div>
    </div>
  );
}

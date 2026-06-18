"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { AppHeader } from "@/components/AppHeader";
import { ReportView } from "@/components/report/ReportView";
import { fetchFeasibilityReport } from "@/lib/feasibility-api";
import type { FeasibilityRow } from "@/lib/feasibility-api";

export default function FeasibilityReportPage() {
  const params = useParams();
  const id = params.id as string;

  const [row, setRow] = useState<FeasibilityRow | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await fetchFeasibilityReport(id);
      setRow(data);
      setError(null);
      return data;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load report");
      return null;
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  // Poll while the pipeline runs.
  useEffect(() => {
    const running = row?.status === "running" || row?.status === "pending";
    if (running && !pollRef.current) {
      pollRef.current = setInterval(async () => {
        const u = await load();
        if (u && u.status !== "running" && u.status !== "pending" && pollRef.current) {
          clearInterval(pollRef.current);
          pollRef.current = null;
        }
      }, 4000);
    }
    if (!running && pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [row?.status, load]);

  function Frame({ children }: { children: React.ReactNode }) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] text-white">
        <div className="print:hidden">
          <AppHeader />
        </div>
        <div className="pt-[72px] print:pt-0 max-w-4xl mx-auto px-6 py-8">{children}</div>
      </div>
    );
  }

  if (loading) {
    return (
      <Frame>
        <div className="flex flex-col items-center justify-center py-32 gap-4">
          <div className="w-8 h-8 border-2 border-white/20 border-t-white/80 rounded-full animate-spin" />
          <p className="text-white/50 text-sm">Loading study…</p>
        </div>
      </Frame>
    );
  }

  if (error && !row) {
    return (
      <Frame>
        <div className="text-center py-32">
          <p className="text-red-400 mb-4">{error}</p>
          <Link href="/report" className="text-white/50 hover:text-white text-sm underline">Start a new study</Link>
        </div>
      </Frame>
    );
  }

  if (row?.status === "failed") {
    return (
      <Frame>
        <div className="text-center py-32">
          <p className="text-red-400 mb-2">This study could not be completed.</p>
          {row.error && <p className="text-white/40 text-sm mb-4">{row.error}</p>}
          <Link href="/report" className="text-white/50 hover:text-white text-sm underline">Try a new study</Link>
        </div>
      </Frame>
    );
  }

  if (row?.status !== "completed" || !row.report) {
    const step = row?.progress?.step ?? 0;
    const total = row?.progress?.steps_total ?? 7;
    const label = row?.progress?.label ?? "Queued";
    const pct = Math.round((step / total) * 100);
    return (
      <Frame>
        <div className="max-w-md mx-auto py-28 text-center">
          <div className="w-10 h-10 border-2 border-blue-400/30 border-t-blue-400 rounded-full animate-spin mx-auto mb-6" />
          <h2 className="text-lg font-semibold mb-1">Building your feasibility study</h2>
          <p className="text-white/50 text-sm mb-6">{label}…</p>
          <div className="h-2 bg-white/10 rounded-full overflow-hidden">
            <div className="h-full bg-blue-500 rounded-full transition-all duration-500" style={{ width: `${pct}%` }} />
          </div>
          <p className="text-white/30 text-xs mt-2">Step {step} of {total}</p>
          <p className="text-white/30 text-xs mt-6">Analyzing demographics, competition, demand, economics and financials. This usually takes a minute or two.</p>
        </div>
      </Frame>
    );
  }

  // completed
  return (
    <Frame>
      {/* action bar (hidden when printing) */}
      <div className="print:hidden flex items-center justify-between mb-6 flex-wrap gap-3">
        <Link href="/report" className="text-white/40 hover:text-white text-sm">&larr; New study</Link>
        <div className="flex items-center gap-3">
          <Link
            href={`/app?feasibility=${id}`}
            className="text-sm px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-white/80 hover:border-white/30 transition-colors"
            title="Open the chat to ask follow-up and what-if questions about this study"
          >
            Ask about this report
          </Link>
          <button
            onClick={() => window.print()}
            className="text-sm px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white transition-colors"
          >
            Download PDF
          </button>
        </div>
      </div>

      <div className="mb-6">
        <h1 className="text-2xl font-bold">{row.report.meta.title}</h1>
        <p className="text-white/40 text-sm">
          Generated {new Date(row.report.meta.generated_at).toLocaleDateString()} · PHOW Feasibility Study
        </p>
      </div>

      <ReportView report={row.report} />
    </Frame>
  );
}

"use client";

import { MarketValidatorWidget } from "@/components/tools/MarketValidatorWidget";
import type { FeasibilityReport, SourceRef } from "@/lib/feasibility-api";

// ---------------------------------------------------------------------------
// small presentational helpers (self-contained — no external prop contracts)
// ---------------------------------------------------------------------------

function money(v?: number | null): string {
  if (v == null) return "N/A";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(v);
}

function Section({ id, title, subtitle, children }: { id: string; title: string; subtitle?: string; children: React.ReactNode }) {
  return (
    <section id={id} className="scroll-mt-24 print:break-inside-avoid">
      <div className="mb-3">
        <h2 className="text-lg font-semibold text-white">{title}</h2>
        {subtitle && <p className="text-sm text-white/40">{subtitle}</p>}
      </div>
      {children}
    </section>
  );
}

function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <div className={`dark-card p-5 ${className}`}>{children}</div>;
}

function Stat({ label, value, sub }: { label: string; value: React.ReactNode; sub?: string }) {
  return (
    <div className="bg-white/5 border border-white/10 rounded-lg p-4">
      <p className="text-xs text-white/40 uppercase tracking-wide mb-1">{label}</p>
      <p className="text-xl font-semibold text-white">{value}</p>
      {sub && <p className="text-xs text-white/40 mt-1">{sub}</p>}
    </div>
  );
}

function Bar({ label, value, max = 100, color }: { label: string; value: number; max?: number; color: string }) {
  const pct = Math.max(0, Math.min(100, (value / max) * 100));
  return (
    <div>
      <div className="flex justify-between text-xs text-white/60 mb-1">
        <span>{label}</span>
        <span className="text-white/80 font-medium">{Math.round(value)}</span>
      </div>
      <div className="h-2 bg-white/10 rounded-full overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
    </div>
  );
}

function Pills({ items, tone = "neutral" }: { items: string[]; tone?: "good" | "bad" | "neutral" }) {
  const cls =
    tone === "good"
      ? "bg-emerald-500/10 text-emerald-300 border-emerald-500/20"
      : tone === "bad"
      ? "bg-red-500/10 text-red-300 border-red-500/20"
      : "bg-white/5 text-white/70 border-white/10";
  return (
    <div className="flex flex-wrap gap-2">
      {items.map((s, i) => (
        <span key={i} className={`text-xs px-2.5 py-1 rounded-full border ${cls}`}>{s}</span>
      ))}
    </div>
  );
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type W = any;
const get = (v: unknown): W => v as W;
const isUnavailable = (v: unknown): boolean => !v || (typeof v === "object" && (v as W).status === "unavailable");

// ---------------------------------------------------------------------------
// verdict hero
// ---------------------------------------------------------------------------

function VerdictHero({ report }: { report: FeasibilityReport }) {
  const v = report.verdict;
  const style: Record<string, { bg: string; ring: string; text: string; label: string }> = {
    GO: { bg: "from-emerald-600/30 to-emerald-900/10", ring: "border-emerald-500/40", text: "text-emerald-300", label: "GO" },
    GO_WITH_CONDITIONS: { bg: "from-amber-600/30 to-amber-900/10", ring: "border-amber-500/40", text: "text-amber-300", label: "GO — WITH CONDITIONS" },
    NO_GO: { bg: "from-red-600/30 to-red-900/10", ring: "border-red-500/40", text: "text-red-300", label: "NO-GO" },
  };
  const s = style[v.decision] ?? style.GO_WITH_CONDITIONS;
  return (
    <div className={`rounded-2xl border ${s.ring} bg-gradient-to-br ${s.bg} p-6 md:p-8`}>
      <div className="flex flex-col md:flex-row md:items-center gap-6">
        <div className={`flex-shrink-0 w-28 h-28 rounded-full border-4 ${s.ring} flex flex-col items-center justify-center`}>
          <span className="text-4xl font-bold text-white">{v.score}</span>
          <span className="text-[10px] text-white/50 uppercase tracking-wide">score / 100</span>
        </div>
        <div className="flex-1">
          <p className="text-xs text-white/50 uppercase tracking-widest mb-1">Feasibility Verdict</p>
          <h1 className={`text-3xl font-bold ${s.text} mb-2`}>{s.label}</h1>
          <p className="text-sm text-white/70 max-w-2xl">{v.rationale}</p>
          <p className="text-xs text-white/40 mt-2">Confidence: {v.confidence}</p>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// sections
// ---------------------------------------------------------------------------

function ExecSummarySection({ report }: { report: FeasibilityReport }) {
  const es = report.exec_summary;
  if (!es || (!es.summary_paragraphs?.length && !es.key_findings?.length)) return null;
  return (
    <Section id="summary" title="Executive Summary">
      <Card>
        {es.summary_paragraphs?.map((p, i) => (
          <p key={i} className="text-sm text-white/80 leading-relaxed mb-3">{p}</p>
        ))}
        {es.key_findings?.length > 0 && (
          <div className="mt-4 pt-4 border-t border-white/10">
            <h4 className="text-sm font-medium text-white/80 mb-2">Key findings</h4>
            <ul className="space-y-2">
              {es.key_findings.map((f, i) => (
                <li key={i} className="text-sm text-white/70 flex gap-2">
                  <span className="text-blue-400">•</span>
                  <span>{f}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </Card>
    </Section>
  );
}

function MarketSizeSection({ data }: { data: W }) {
  if (!data) return null;
  const tiers = [data.tam, data.sam, data.som].filter(Boolean);
  const maxVal = Math.max(...tiers.map((t: W) => t?.value || 0), 1);
  return (
    <Section id="market-size" title="Market Size" subtitle="Total / Serviceable / Obtainable market">
      <Card className="space-y-4">
        {[
          { d: data.tam, c: "#60a5fa" },
          { d: data.sam, c: "#818cf8" },
          { d: data.som, c: "#34d399" },
        ].map(({ d, c }, i) =>
          d ? (
            <div key={i}>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-white/70">{d.label}</span>
                <span className="text-white font-semibold">{d.formatted}</span>
              </div>
              <div className="h-3 bg-white/10 rounded-full overflow-hidden">
                <div className="h-full rounded-full" style={{ width: `${((d.value || 0) / maxVal) * 100}%`, backgroundColor: c }} />
              </div>
            </div>
          ) : null
        )}
        {data.confidence && <p className="text-xs text-white/40 pt-1">Confidence: {String(data.confidence)}</p>}
      </Card>
    </Section>
  );
}

function CompetitionSection({ comp }: { comp: W }) {
  if (!comp) return null;
  const competitors = get(comp.competitors);
  const swot = get(comp.swot);
  const forces = get(comp.five_forces);
  const pricing = get(comp.pricing);
  const positioning = get(comp.positioning);
  const list: W[] = competitors?.competitors || [];
  return (
    <Section id="competition" title="Competition" subtitle={competitors ? `${competitors.total_found ?? list.length} competitors found nearby` : undefined}>
      <div className="space-y-4">
        {list.length > 0 && (
          <Card>
            <h4 className="text-sm font-medium text-white/80 mb-3">Top competitors (Google + Yelp)</h4>
            <div className="space-y-2">
              {list.slice(0, 6).map((c, i) => (
                <div key={i} className="flex items-center justify-between bg-white/5 border border-white/10 rounded-lg px-3 py-2">
                  <div className="min-w-0">
                    <p className="text-sm text-white/90 truncate">{c.name}</p>
                    {c.address && <p className="text-xs text-white/40 truncate">{c.address}</p>}
                  </div>
                  <div className="text-right flex-shrink-0 ml-3">
                    {c.rating != null && <span className="text-amber-400 text-sm">★ {Number(c.rating).toFixed(1)}</span>}
                    {c.review_count != null && <span className="text-white/40 text-xs ml-1">({c.review_count})</span>}
                    {c.price_level ? <span className="text-emerald-400 text-xs ml-2">{"$".repeat(c.price_level)}</span> : null}
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}

        {swot && (
          <Card>
            <h4 className="text-sm font-medium text-white/80 mb-3">SWOT</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                { k: "strengths", t: "Strengths", tone: "good" as const },
                { k: "weaknesses", t: "Weaknesses", tone: "bad" as const },
                { k: "opportunities", t: "Opportunities", tone: "good" as const },
                { k: "threats", t: "Threats", tone: "bad" as const },
              ].map(({ k, t, tone }) => (
                <div key={k}>
                  <p className={`text-xs font-medium mb-2 ${tone === "good" ? "text-emerald-400" : "text-red-400"}`}>{t}</p>
                  <Pills items={(swot[k] || []).map((x: W) => x.factor).filter(Boolean)} tone={tone} />
                </div>
              ))}
            </div>
          </Card>
        )}

        {forces?.forces && (
          <Card>
            <h4 className="text-sm font-medium text-white/80 mb-3">
              Porter&apos;s Five Forces
              {forces.overall?.level && <span className="text-white/40 font-normal"> · {forces.overall.level}</span>}
            </h4>
            <div className="space-y-2.5">
              {forces.forces.map((f: W, i: number) => (
                <Bar key={i} label={f.name} value={f.score} color={f.score >= 70 ? "#ef4444" : f.score >= 40 ? "#f59e0b" : "#34d399"} />
              ))}
            </div>
          </Card>
        )}

        {(pricing || positioning) && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {pricing && (
              <Card>
                <h4 className="text-sm font-medium text-white/80 mb-3">Pricing landscape</h4>
                <div className="flex items-end gap-3 h-24 mb-2">
                  {(pricing.chart_data || []).map((d: W, i: number) => {
                    const maxC = Math.max(...(pricing.chart_data || []).map((x: W) => x.count || 0), 1);
                    return (
                      <div key={i} className="flex-1 flex flex-col items-center justify-end h-full">
                        <div className="w-full bg-blue-500/40 rounded-t" style={{ height: `${((d.count || 0) / maxC) * 100}%` }} />
                        <span className="text-xs text-white/50 mt-1">{d.tier}</span>
                      </div>
                    );
                  })}
                </div>
                {pricing.recommendation && <p className="text-xs text-white/50">{pricing.recommendation}</p>}
              </Card>
            )}
            {positioning && (
              <Card>
                <h4 className="text-sm font-medium text-white/80 mb-3">Market gaps</h4>
                {(positioning.market_gaps || []).length > 0 ? (
                  <ul className="space-y-2">
                    {positioning.market_gaps.map((g: string, i: number) => (
                      <li key={i} className="text-sm text-white/70 flex gap-2"><span className="text-emerald-400">↗</span>{g}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-white/40">No obvious positioning gaps.</p>
                )}
                {positioning.recommendation && <p className="text-xs text-white/50 mt-3 pt-3 border-t border-white/10">{positioning.recommendation}</p>}
              </Card>
            )}
          </div>
        )}
      </div>
    </Section>
  );
}

function FinancialSection({ fin }: { fin: W }) {
  if (!fin) return null;
  const sc = fin.revenue_scenarios || {};
  const be = fin.break_even || {};
  return (
    <Section id="financial" title="Financial Projection" subtitle="Modeled from industry benchmarks (NAICS)">
      <div className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {[
            { k: "conservative", t: "Conservative" },
            { k: "moderate", t: "Moderate" },
            { k: "optimistic", t: "Optimistic" },
          ].map(({ k, t }) => (
            <Stat key={k} label={t} value={money(sc[k]?.annual_revenue)} sub={`${money(sc[k]?.monthly_revenue)}/mo`} />
          ))}
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          <Stat label="Break-even revenue" value={money(be.monthly_revenue_needed)} sub="per month" />
          <Stat label="Covers needed" value={be.transactions_needed_daily ?? "N/A"} sub="per day" />
          <Stat label="Recoup startup" value={be.months_to_recover_startup != null ? `${be.months_to_recover_startup} mo` : "N/A"} />
        </div>
        {Array.isArray(fin.key_insights) && fin.key_insights.length > 0 && (
          <Card>
            <ul className="space-y-2">
              {fin.key_insights.map((s: string, i: number) => (
                <li key={i} className="text-sm text-white/70 flex gap-2"><span className="text-blue-400">•</span>{s}</li>
              ))}
            </ul>
          </Card>
        )}
      </div>
    </Section>
  );
}

function ConsumerSection({ consumer }: { consumer: W }) {
  if (!consumer) return null;
  const sentiment = get(consumer.sentiment);
  const pain = get(consumer.pain_points);
  if (!consumer.data_available) {
    return (
      <Section id="consumer" title="Customer Insights">
        <Card><p className="text-sm text-white/40">No competitor reviews were available to mine for this area.</p></Card>
      </Section>
    );
  }
  return (
    <Section id="consumer" title="Customer Insights" subtitle={`Mined from ${consumer.reviews_analyzed ?? 0} competitor reviews`}>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {sentiment && (
          <Card>
            <h4 className="text-sm font-medium text-white/80 mb-2">Sentiment</h4>
            <p className="text-2xl font-bold text-white capitalize">{sentiment.sentiment_label}</p>
            {sentiment.average_rating != null && <p className="text-xs text-white/40">Avg rating {Number(sentiment.average_rating).toFixed(1)} · {sentiment.review_count} reviews</p>}
          </Card>
        )}
        {pain && (pain.pain_points || []).length > 0 && (
          <Card>
            <h4 className="text-sm font-medium text-white/80 mb-2">What customers complain about</h4>
            <Pills items={pain.pain_points.slice(0, 6).map((p: W) => p.issue).filter(Boolean)} tone="bad" />
          </Card>
        )}
      </div>
    </Section>
  );
}

function EconomicSection({ econ }: { econ: W }) {
  if (!econ) return null;
  const snap = get(econ.snapshot);
  const seas = get(econ.seasonality);
  const timing = get(econ.entry_timing);
  return (
    <Section id="economic" title="Economic Climate & Timing">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {snap && (
          <Card>
            <h4 className="text-sm font-medium text-white/80 mb-2">Outlook</h4>
            <p className="text-xl font-bold text-white capitalize">{snap.outlook?.level ?? "—"}</p>
            <p className="text-xs text-white/50 mt-1">{snap.outlook?.summary}</p>
          </Card>
        )}
        {seas && (
          <Card>
            <h4 className="text-sm font-medium text-white/80 mb-2">Seasonality</h4>
            <p className="text-sm text-white/70">Peak: <span className="text-emerald-400">{seas.peak_month}</span></p>
            <p className="text-sm text-white/70">Slow: <span className="text-amber-400">{seas.low_month}</span></p>
          </Card>
        )}
        {timing && (
          <Card>
            <h4 className="text-sm font-medium text-white/80 mb-2">Entry timing</h4>
            <p className="text-xl font-bold text-white">{timing.timing_score}/100</p>
            <p className="text-xs text-white/50 mt-1">{timing.recommendation}</p>
          </Card>
        )}
      </div>
    </Section>
  );
}

function FnbSignalsSection({ sig }: { sig: W }) {
  if (!sig) return null;
  const health = sig.health_inspections;
  const walk = sig.walkability;
  const trends = sig.search_trends;
  const cards: React.ReactNode[] = [];
  if (!isUnavailable(health)) cards.push(<Stat key="h" label="Area health scores" value={health.avg_score != null ? `${Math.round(health.avg_score)}` : (health.health_rating ?? "—")} sub={`${health.total_restaurants ?? 0} nearby restaurants`} />);
  if (!isUnavailable(walk)) cards.push(<Stat key="w" label="Walk Score" value={walk.walkscore ?? "—"} sub={walk.transit_score != null ? `Transit ${walk.transit_score}` : undefined} />);
  if (!isUnavailable(trends)) cards.push(<Stat key="t" label="Search interest" value={<span className="capitalize">{trends.momentum ?? "—"}</span>} sub="Google Trends" />);
  if (cards.length === 0) return null;
  return (
    <Section id="fnb" title="Food & Drink Signals">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">{cards}</div>
    </Section>
  );
}

function RecommendationsSection({ recs }: { recs: W[] }) {
  if (!recs || recs.length === 0) return null;
  const order: Record<string, number> = { high: 0, medium: 1, low: 2 };
  const sorted = [...recs].sort((a, b) => (order[a.priority] ?? 1) - (order[b.priority] ?? 1));
  return (
    <Section id="recommendations" title="Recommended Next Steps">
      <div className="space-y-3">
        {sorted.map((r, i) => (
          <Card key={i}>
            <div className="flex items-start gap-3">
              <span className={`text-[10px] uppercase px-2 py-0.5 rounded-full flex-shrink-0 mt-0.5 ${r.priority === "high" ? "bg-red-500/15 text-red-300" : r.priority === "low" ? "bg-white/10 text-white/50" : "bg-amber-500/15 text-amber-300"}`}>{r.priority || "medium"}</span>
              <div>
                <p className="text-sm font-medium text-white">{r.title}</p>
                <p className="text-sm text-white/60 mt-0.5">{r.description}</p>
                {r.rationale && <p className="text-xs text-white/40 mt-1">Why: {r.rationale}</p>}
              </div>
            </div>
          </Card>
        ))}
      </div>
    </Section>
  );
}

function SourcesSection({ sources }: { sources: SourceRef[] }) {
  if (!sources || sources.length === 0) return null;
  return (
    <Section id="sources" title="Sources & Confidence">
      <Card>
        <div className="space-y-2">
          {sources.map((s, i) => (
            <div key={i} className="flex items-start justify-between gap-3 text-sm border-b border-white/5 last:border-0 pb-2 last:pb-0">
              <div>
                <span className="text-white/80">{s.label}</span>
                <span className="text-white/40"> — {s.detail}</span>
              </div>
              <span className={`text-xs flex-shrink-0 ${s.confidence === "high" ? "text-emerald-400" : s.confidence === "low" ? "text-amber-400" : "text-blue-400"}`}>{s.confidence}</span>
            </div>
          ))}
        </div>
      </Card>
    </Section>
  );
}

// ---------------------------------------------------------------------------
// main
// ---------------------------------------------------------------------------

export function ReportView({ report }: { report: FeasibilityReport }) {
  const s = report.sections;
  return (
    <div className="space-y-8">
      <VerdictHero report={report} />
      <ExecSummarySection report={report} />
      {s.location ? (
        <Section id="location" title="Location & Viability">
          {/* MarketValidatorWidget already matches the calculate_market_viability shape */}
          <MarketValidatorWidget data={get(s.location)} />
        </Section>
      ) : null}
      <MarketSizeSection data={get(s.market_size)} />
      <CompetitionSection comp={get(s.competition)} />
      <FinancialSection fin={get(s.financial)} />
      <ConsumerSection consumer={get(s.consumer)} />
      <EconomicSection econ={get(s.economic)} />
      <FnbSignalsSection sig={get(s.fnb_signals)} />
      <RecommendationsSection recs={get(s.recommendations) || []} />
      <SourcesSection sources={report.sources} />
    </div>
  );
}

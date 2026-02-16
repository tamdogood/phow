"use client";

import { useState, useEffect, useMemo, useCallback, useRef } from "react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import {
  GoogleMap,
  useJsApiLoader,
  Marker,
  InfoWindow,
  OverlayView,
} from "@react-google-maps/api";
import { AppHeader } from "@/components/AppHeader";
import {
  fetchSearchGridReport,
  updateSearchGridReport,
  deleteSearchGridReport,
  triggerSearchGridRun,
  fetchSearchGridRunResults,
  fetchSearchGridResultDetail,
  fetchSearchGridCompetitors,
  addCompetitor,
} from "@/lib/api";
import { getSessionId } from "@/lib/session";
import { useAuth } from "@/contexts/AuthContext";
import { SearchGridReportWithResults, SearchGridResult, SearchGridResultDetail, AggregatedCompetitor } from "@/types";
import { GOOGLE_MAPS_LIBRARIES, GOOGLE_MAPS_API_KEY } from "@/lib/google-maps";

// ---------------------------------------------------------------------------
// Haversine distance
// ---------------------------------------------------------------------------

function haversineKm(lat1: number, lng1: number, lat2: number, lng2: number): number {
  const R = 6371;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLng = ((lng2 - lng1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180) * Math.sin(dLng / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function formatDistance(km: number): string {
  return km < 1 ? `${Math.round(km * 1000)}m` : `${km.toFixed(1)}km`;
}

// ---------------------------------------------------------------------------
// Grid calculation
// ---------------------------------------------------------------------------

function calculateGridPoints(
  centerLat: number,
  centerLng: number,
  radiusKm: number,
  gridSize: number
) {
  const stepKm = (radiusKm * 2) / (gridSize - 1);
  const half = Math.floor(gridSize / 2);
  const latStep = stepKm / 111.32;
  const lngStep = stepKm / (111.32 * Math.cos((centerLat * Math.PI) / 180));
  const points: { row: number; col: number; lat: number; lng: number }[] = [];
  for (let row = 0; row < gridSize; row++) {
    for (let col = 0; col < gridSize; col++) {
      points.push({
        row,
        col,
        lat: centerLat + (row - half) * latStep,
        lng: centerLng + (col - half) * lngStep,
      });
    }
  }
  return points;
}

// ---------------------------------------------------------------------------
// Score helpers
// ---------------------------------------------------------------------------

function computeFallbackScore(rank: number | null, totalResults: number): number {
  let visibility = 0;
  if (rank !== null && rank >= 1 && rank <= 20) {
    visibility = Math.round(50 - (rank - 1) * (47 / 19));
  }
  let opportunity = 5;
  if (totalResults === 0) opportunity = 30;
  else if (totalResults <= 5) opportunity = 25;
  else if (totalResults <= 10) opportunity = 15;
  return Math.max(0, Math.min(100, visibility + opportunity + 10));
}

function getScore(result: SearchGridResult | SearchGridResultDetail | null | undefined): number | null {
  if (!result) return null;
  return result.score ?? computeFallbackScore(result.rank, result.total_results);
}

function scoreColor(score: number | null): string {
  if (score == null) return "#6b7280";
  if (score >= 70) return "#22c55e";
  if (score >= 45) return "#3b82f6";
  if (score >= 25) return "#f59e0b";
  return "#ef4444";
}

function scoreLabel(score: number | null): string {
  return score != null ? `${score}` : "—";
}

// ---------------------------------------------------------------------------
// Map config
// ---------------------------------------------------------------------------

const mapContainerStyle = { width: "100%", height: "100%" };

const mapOptions: google.maps.MapOptions = {
  disableDefaultUI: true,
  zoomControl: true,
  styles: [
    { elementType: "geometry", stylers: [{ color: "#1a1a2e" }] },
    { elementType: "labels.text.stroke", stylers: [{ color: "#1a1a2e" }] },
    { elementType: "labels.text.fill", stylers: [{ color: "#6b7280" }] },
    { featureType: "road", elementType: "geometry", stylers: [{ color: "#2d2d44" }] },
    { featureType: "road", elementType: "labels.text.fill", stylers: [{ color: "#6b7280" }] },
    { featureType: "road.highway", elementType: "geometry", stylers: [{ color: "#3d3d5c" }] },
    { featureType: "water", elementType: "geometry", stylers: [{ color: "#0c3654" }] },
    { featureType: "poi", elementType: "labels", stylers: [{ visibility: "off" }] },
    { featureType: "poi.park", elementType: "geometry", stylers: [{ color: "#1a2e1a" }] },
    { featureType: "transit", stylers: [{ visibility: "off" }] },
  ],
};

// ---------------------------------------------------------------------------
// Status badge
// ---------------------------------------------------------------------------

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { bg: string; text: string; label: string }> = {
    running: { bg: "bg-blue-500/20", text: "text-blue-400", label: "Running" },
    completed: { bg: "bg-emerald-500/20", text: "text-emerald-400", label: "Completed" },
    failed: { bg: "bg-red-500/20", text: "text-red-400", label: "Failed" },
    pending: { bg: "bg-amber-500/20", text: "text-amber-400", label: "Pending" },
  };
  const s = map[status] ?? { bg: "bg-white/10", text: "text-white/60", label: status };
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${s.bg} ${s.text}`}>
      {status === "running" && (
        <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
      )}
      {s.label}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Page component
// ---------------------------------------------------------------------------

export default function SearchGridReportPage() {
  const router = useRouter();
  const params = useParams();
  const { user } = useAuth();
  const reportId = params.reportId as string;

  // State
  const [report, setReport] = useState<SearchGridReportWithResults | null>(null);
  const [results, setResults] = useState<SearchGridResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [triggering, setTriggering] = useState(false);
  const [selectedKeyword, setSelectedKeyword] = useState<string>("all");
  const [hoveredPoint, setHoveredPoint] = useState<SearchGridResult | null>(null);
  const [detailPanel, setDetailPanel] = useState<SearchGridResultDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [competitors, setCompetitors] = useState<AggregatedCompetitor[]>([]);
  const [competitorsLoading, setCompetitorsLoading] = useState(false);
  const [trackedIds, setTrackedIds] = useState<Set<string>>(new Set());
  const [trackingId, setTrackingId] = useState<string | null>(null);

  // Editable fields
  const [name, setName] = useState("");
  const [radiusKm, setRadiusKm] = useState(5);
  const [gridSize, setGridSize] = useState(5);
  const [keywords, setKeywords] = useState<string[]>([]);
  const [keywordInput, setKeywordInput] = useState("");
  const [frequency, setFrequency] = useState("weekly");

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Google Maps
  const { isLoaded } = useJsApiLoader({
    googleMapsApiKey: GOOGLE_MAPS_API_KEY,
    libraries: GOOGLE_MAPS_LIBRARIES,
  });

  // -------------------------------------------------------------------
  // Fetch report
  // -------------------------------------------------------------------

  const loadReport = useCallback(async () => {
    try {
      const data = await fetchSearchGridReport(reportId);
      setReport(data);
      setResults(data.results ?? []);
      setName(data.name);
      setRadiusKm(data.radius_km);
      setGridSize(data.grid_size);
      setKeywords(data.keywords);
      setFrequency(data.frequency);
      setError(null);
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load report");
      return null;
    } finally {
      setLoading(false);
    }
  }, [reportId]);

  // Initial load
  useEffect(() => {
    loadReport();
  }, [loadReport]);

  // -------------------------------------------------------------------
  // Polling while running
  // -------------------------------------------------------------------

  useEffect(() => {
    const isRunning = report?.latest_run?.status === "running" || report?.status === "running";

    if (isRunning && !pollRef.current) {
      pollRef.current = setInterval(async () => {
        const updated = await loadReport();
        if (updated && updated.latest_run?.status !== "running" && updated.status !== "running") {
          if (pollRef.current) {
            clearInterval(pollRef.current);
            pollRef.current = null;
          }
        }
      }, 5000);
    }

    if (!isRunning && pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }

    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [report?.latest_run?.status, report?.status, loadReport]);

  // -------------------------------------------------------------------
  // Fetch aggregated competitors
  // -------------------------------------------------------------------

  useEffect(() => {
    const runId = report?.latest_run?.id;
    const runStatus = report?.latest_run?.status;
    if (!runId || runStatus !== "completed") {
      setCompetitors([]);
      return;
    }
    let cancelled = false;
    setCompetitorsLoading(true);
    const kw = selectedKeyword === "all" ? undefined : selectedKeyword;
    fetchSearchGridCompetitors(runId, kw)
      .then((data) => { if (!cancelled) setCompetitors(data); })
      .catch(() => { if (!cancelled) setCompetitors([]); })
      .finally(() => { if (!cancelled) setCompetitorsLoading(false); });
    return () => { cancelled = true; };
  }, [report?.latest_run?.id, report?.latest_run?.status, selectedKeyword]);

  // -------------------------------------------------------------------
  // Filtered results
  // -------------------------------------------------------------------

  const filteredResults = useMemo(() => {
    if (selectedKeyword === "all") return results;
    return results.filter((r) => r.keyword === selectedKeyword);
  }, [results, selectedKeyword]);

  // Grid points for map overlay
  const gridPoints = useMemo(() => {
    if (!report) return [];
    return calculateGridPoints(report.center_lat, report.center_lng, radiusKm, gridSize);
  }, [report, radiusKm, gridSize]);

  // Map center
  const mapCenter = useMemo(
    () => (report ? { lat: report.center_lat, lng: report.center_lng } : { lat: 37.7749, lng: -122.4194 }),
    [report]
  );

  // Build lookup: "row-col" -> best rank result
  const resultLookup = useMemo(() => {
    const map = new Map<string, SearchGridResult>();
    for (const r of filteredResults) {
      const key = `${r.grid_row}-${r.grid_col}`;
      const existing = map.get(key);
      if (!existing || (r.rank !== null && (existing.rank === null || r.rank < existing.rank))) {
        map.set(key, r);
      }
    }
    return map;
  }, [filteredResults]);

  // -------------------------------------------------------------------
  // Summary stats
  // -------------------------------------------------------------------

  const stats = useMemo(() => {
    const ranked = filteredResults.filter((r) => r.rank !== null);
    const withScores = filteredResults.map((r) => ({ ...r, _score: getScore(r) })).filter((r) => r._score != null);
    const avgRank = ranked.length
      ? Math.round((ranked.reduce((s, r) => s + (r.rank ?? 0), 0) / ranked.length) * 10) / 10
      : null;
    const top3 = ranked.filter((r) => r.rank !== null && r.rank <= 3).length;
    const avgScore = withScores.length
      ? Math.round(withScores.reduce((s, r) => s + r._score!, 0) / withScores.length)
      : null;
    return {
      avgRank,
      avgScore,
      top3Pct: filteredResults.length ? Math.round((top3 / filteredResults.length) * 100) : 0,
      coverage: filteredResults.length ? Math.round((ranked.length / filteredResults.length) * 100) : 0,
    };
  }, [filteredResults]);

  // -------------------------------------------------------------------
  // Actions
  // -------------------------------------------------------------------

  async function handleSave() {
    setSaving(true);
    try {
      await updateSearchGridReport(reportId, {
        name,
        radius_km: radiusKm,
        grid_size: gridSize,
        keywords,
        frequency,
      });
      await loadReport();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    setDeleting(true);
    try {
      await deleteSearchGridReport(reportId);
      router.push("/search-grid");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete");
      setDeleting(false);
    }
  }

  async function handleRunNow() {
    setTriggering(true);
    try {
      await triggerSearchGridRun(reportId);
      await loadReport();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to trigger run");
    } finally {
      setTriggering(false);
    }
  }

  function addKeyword() {
    const kw = keywordInput.trim();
    if (kw && !keywords.includes(kw)) {
      setKeywords([...keywords, kw]);
    }
    setKeywordInput("");
  }

  function removeKeyword(kw: string) {
    setKeywords(keywords.filter((k) => k !== kw));
  }

  async function handleGridPointClick(result: SearchGridResult) {
    if (!result.id) return;
    setDetailLoading(true);
    try {
      const detail = await fetchSearchGridResultDetail(result.id);
      setDetailPanel(detail);
    } catch {
      setDetailPanel(null);
    } finally {
      setDetailLoading(false);
    }
  }

  async function handleTrackCompetitor(comp: AggregatedCompetitor) {
    if (!comp.place_id || trackedIds.has(comp.place_id)) return;
    setTrackingId(comp.place_id);
    try {
      await addCompetitor({
        session_id: user?.id || getSessionId(),
        place_id: comp.place_id,
        name: comp.name,
        rating: comp.rating ?? undefined,
        review_count: comp.user_ratings_total ?? undefined,
      });
      setTrackedIds((prev) => new Set(prev).add(comp.place_id));
    } catch {
      // silently fail — user can retry
    } finally {
      setTrackingId(null);
    }
  }

  // -------------------------------------------------------------------
  // Loading state
  // -------------------------------------------------------------------

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-2 border-white/20 border-t-white/80 rounded-full animate-spin" />
          <p className="text-white/50 text-sm">Loading report...</p>
        </div>
      </div>
    );
  }

  if (error && !report) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 mb-4">{error}</p>
          <Link href="/search-grid" className="text-white/50 hover:text-white text-sm underline">
            Back to reports
          </Link>
        </div>
      </div>
    );
  }

  const isRunning = report?.latest_run?.status === "running" || report?.status === "running";
  const runStatus = report?.latest_run?.status ?? report?.status ?? "idle";

  // -------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      <AppHeader maxWidth="max-w-[1600px]" />

      {/* Main layout */}
      <div className="pt-[72px] flex h-[calc(100vh-72px)]">
        {/* Sidebar */}
        <aside className="w-[380px] flex-shrink-0 border-r border-white/10 overflow-y-auto p-6 space-y-6">
          {/* Status + actions */}
          <div className="flex items-center gap-3 flex-wrap">
            <StatusBadge status={runStatus} />
            {report?.latest_run && (
              <span className="text-xs text-white/30">
                {report.latest_run.points_completed}/{report.latest_run.points_total} points
              </span>
            )}
          </div>

          {/* Run history / latest run info */}
          {report?.latest_run && (
            <div className="dark-card p-4 space-y-2">
              <label className="text-xs text-white/50 font-medium">Latest Run</label>
              <div className="text-sm text-white/80">
                {report.latest_run.started_at
                  ? new Date(report.latest_run.started_at).toLocaleString()
                  : "N/A"}
              </div>
              {report.latest_run.avg_rank !== null && (
                <div className="text-xs text-white/50">
                  Avg rank: {report.latest_run.avg_rank} | Top 3: {report.latest_run.top3_pct}%
                </div>
              )}
            </div>
          )}

          {/* Stats */}
          {filteredResults.length > 0 && (
            <div className="grid grid-cols-2 gap-3">
              <div className="dark-card p-3 text-center">
                <p className="text-xs text-white/50">Avg Score</p>
                <p className="text-lg font-bold" style={{ color: scoreColor(stats.avgScore) }}>
                  {stats.avgScore ?? "--"}
                </p>
              </div>
              <div className="dark-card p-3 text-center">
                <p className="text-xs text-white/50">Avg Rank</p>
                <p className="text-lg font-bold text-white">{stats.avgRank ?? "--"}</p>
              </div>
              <div className="dark-card p-3 text-center">
                <p className="text-xs text-white/50">Top 3</p>
                <p className="text-lg font-bold text-emerald-400">{stats.top3Pct}%</p>
              </div>
              <div className="dark-card p-3 text-center">
                <p className="text-xs text-white/50">Coverage</p>
                <p className="text-lg font-bold text-blue-400">{stats.coverage}%</p>
              </div>
            </div>
          )}

          {/* Keyword filter */}
          {report && report.keywords.length > 0 && (
            <div>
              <label className="text-xs text-white/50 font-medium block mb-2">Filter by Keyword</label>
              <select
                value={selectedKeyword}
                onChange={(e) => setSelectedKeyword(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-white/30"
              >
                <option value="all">All keywords</option>
                {report.keywords.map((kw) => (
                  <option key={kw} value={kw}>
                    {kw}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Divider */}
          <div className="border-t border-white/10" />

          {/* Editable settings */}
          <div className="space-y-4">
            <h3 className="text-sm font-medium text-white/80">Report Settings</h3>

            {/* Name */}
            <div>
              <label className="text-xs text-white/50 block mb-1">Report Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-white/30"
              />
            </div>

            {/* Location (read-only) */}
            <div>
              <label className="text-xs text-white/50 block mb-1">Center Location</label>
              <p className="text-sm text-white/60 bg-white/5 border border-white/10 rounded-lg px-3 py-2">
                {report?.center_address ?? `${report?.center_lat}, ${report?.center_lng}`}
              </p>
            </div>

            {/* Radius */}
            <div>
              <label className="text-xs text-white/50 block mb-1">Radius: {radiusKm} km</label>
              <input
                type="range"
                min={1}
                max={30}
                step={1}
                value={radiusKm}
                onChange={(e) => setRadiusKm(Number(e.target.value))}
                className="w-full accent-blue-500"
              />
              <div className="flex justify-between text-[10px] text-white/30">
                <span>1 km</span>
                <span>30 km</span>
              </div>
            </div>

            {/* Grid size */}
            <div>
              <label className="text-xs text-white/50 block mb-1">Grid Size: {gridSize}x{gridSize}</label>
              <input
                type="range"
                min={3}
                max={9}
                step={2}
                value={gridSize}
                onChange={(e) => setGridSize(Number(e.target.value))}
                className="w-full accent-blue-500"
              />
              <div className="flex justify-between text-[10px] text-white/30">
                <span>3x3</span>
                <span>9x9</span>
              </div>
            </div>

            {/* Keywords */}
            <div>
              <label className="text-xs text-white/50 block mb-1">Keywords</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={keywordInput}
                  onChange={(e) => setKeywordInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addKeyword())}
                  placeholder="Add keyword..."
                  className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder:text-white/30 focus:outline-none focus:border-white/30"
                />
                <button
                  onClick={addKeyword}
                  className="px-3 py-2 bg-white/10 hover:bg-white/15 rounded-lg text-sm text-white transition-colors"
                >
                  +
                </button>
              </div>
              {keywords.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-2">
                  {keywords.map((kw) => (
                    <span
                      key={kw}
                      className="inline-flex items-center gap-1 px-2 py-1 bg-white/10 rounded-md text-xs text-white/80"
                    >
                      {kw}
                      <button
                        onClick={() => removeKeyword(kw)}
                        className="text-white/40 hover:text-white/80 ml-0.5"
                      >
                        x
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Frequency */}
            <div>
              <label className="text-xs text-white/50 block mb-1">Frequency</label>
              <select
                value={frequency}
                onChange={(e) => setFrequency(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-white/30"
              >
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="biweekly">Biweekly</option>
                <option value="monthly">Monthly</option>
              </select>
            </div>
          </div>

          {/* Error banner */}
          {error && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-3 text-sm text-red-400">
              {error}
            </div>
          )}

          {/* Action buttons */}
          <div className="space-y-3">
            <div className="flex gap-3">
              <button
                onClick={handleSave}
                disabled={saving}
                className="flex-1 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium py-2.5 rounded-lg transition-colors"
              >
                {saving ? "Saving..." : "Save Changes"}
              </button>
              <button
                onClick={handleRunNow}
                disabled={triggering || isRunning}
                className="flex-1 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium py-2.5 rounded-lg transition-colors"
              >
                {triggering ? "Starting..." : isRunning ? "Running..." : "Run Now"}
              </button>
            </div>

            {/* Delete */}
            {!confirmDelete ? (
              <button
                onClick={() => setConfirmDelete(true)}
                className="w-full text-red-400/60 hover:text-red-400 text-xs py-2 transition-colors"
              >
                Delete Report
              </button>
            ) : (
              <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 space-y-2">
                <p className="text-xs text-red-400">
                  Are you sure? This will permanently delete this report and all run data.
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={handleDelete}
                    disabled={deleting}
                    className="flex-1 bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white text-xs font-medium py-2 rounded-lg transition-colors"
                  >
                    {deleting ? "Deleting..." : "Yes, Delete"}
                  </button>
                  <button
                    onClick={() => setConfirmDelete(false)}
                    className="flex-1 bg-white/10 hover:bg-white/15 text-white text-xs py-2 rounded-lg transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        </aside>

        {/* Map area */}
        <main className="flex-1 relative">
          {!isLoaded ? (
            <div className="absolute inset-0 flex items-center justify-center bg-[#0a0a0a]">
              <div className="w-6 h-6 border-2 border-white/20 border-t-white/80 rounded-full animate-spin" />
            </div>
          ) : (
            <GoogleMap
              mapContainerStyle={mapContainerStyle}
              center={mapCenter}
              zoom={12}
              options={mapOptions}
            >
              {/* Center marker */}
              <Marker
                position={mapCenter}
                icon={{
                  path: google.maps.SymbolPath.CIRCLE,
                  scale: 6,
                  fillColor: "#3b82f6",
                  fillOpacity: 1,
                  strokeColor: "#1d4ed8",
                  strokeWeight: 2,
                }}
              />

              {/* Grid result circles */}
              {gridPoints.map((pt) => {
                const key = `${pt.row}-${pt.col}`;
                const result = resultLookup.get(key);
                const score = getScore(result);
                const color = scoreColor(score);

                return (
                  <OverlayView
                    key={key}
                    position={{ lat: pt.lat, lng: pt.lng }}
                    mapPaneName={OverlayView.OVERLAY_MOUSE_TARGET}
                  >
                    <div
                      className="flex items-center justify-center cursor-pointer"
                      style={{
                        width: 32,
                        height: 32,
                        marginLeft: -16,
                        marginTop: -16,
                        borderRadius: "50%",
                        backgroundColor: color,
                        opacity: result ? 0.9 : 0.3,
                        border: "2px solid rgba(255,255,255,0.3)",
                        fontSize: 10,
                        fontWeight: 700,
                        color: "#fff",
                        textShadow: "0 1px 2px rgba(0,0,0,0.5)",
                      }}
                      onClick={() => result && handleGridPointClick(result)}
                      onMouseEnter={() => result && setHoveredPoint(result)}
                      onMouseLeave={() => setHoveredPoint(null)}
                    >
                      {result ? scoreLabel(score) : ""}
                    </div>
                  </OverlayView>
                );
              })}

              {/* Info window on hover */}
              {hoveredPoint && (
                <InfoWindow
                  position={{ lat: hoveredPoint.point_lat, lng: hoveredPoint.point_lng }}
                  options={{ disableAutoPan: true, pixelOffset: new google.maps.Size(0, -20) }}
                  onCloseClick={() => setHoveredPoint(null)}
                >
                  <div className="text-xs text-gray-900 space-y-1 min-w-[160px]">
                    <p className="font-semibold">{hoveredPoint.keyword}</p>
                    <p>
                      Score: <span className="font-bold">{scoreLabel(getScore(hoveredPoint))}</span>
                      {hoveredPoint.rank !== null && (
                        <span className="ml-2 text-gray-500">Rank #{hoveredPoint.rank}</span>
                      )}
                    </p>
                    <p className="text-gray-500">{hoveredPoint.total_results} competitors nearby</p>
                    {hoveredPoint.top_result_name && (
                      <p className="text-gray-500">Top: {hoveredPoint.top_result_name}</p>
                    )}
                  </div>
                </InfoWindow>
              )}
            </GoogleMap>
          )}

          {/* Map legend */}
          <div className="absolute bottom-6 left-6 dark-card p-4 space-y-2 pointer-events-auto">
            <p className="text-xs font-medium text-white/80">Score</p>
            <div className="flex items-center gap-3 text-xs">
              {[
                { color: "#22c55e", label: "70+" },
                { color: "#3b82f6", label: "45-69" },
                { color: "#f59e0b", label: "25-44" },
                { color: "#ef4444", label: "<25" },
                { color: "#6b7280", label: "N/A" },
              ].map((item) => (
                <div key={item.label} className="flex items-center gap-1.5">
                  <span className="inline-block w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                  <span className="text-white/60">{item.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Running overlay */}
          {isRunning && (
            <div className="absolute top-6 left-1/2 -translate-x-1/2 dark-card px-5 py-3 flex items-center gap-3">
              <div className="w-4 h-4 border-2 border-blue-400/30 border-t-blue-400 rounded-full animate-spin" />
              <span className="text-sm text-white/80">
                Analysis running... {report?.latest_run?.points_completed ?? 0}/
                {report?.latest_run?.points_total ?? 0} points
              </span>
            </div>
          )}
        </main>

        {/* Detail slide-out panel */}
        {(detailPanel || detailLoading) ? (
          <aside className="w-[400px] flex-shrink-0 border-l border-white/10 overflow-y-auto bg-[#0a0a0a]">
            {detailLoading ? (
              <div className="flex items-center justify-center h-40">
                <div className="w-5 h-5 border-2 border-white/20 border-t-white/80 rounded-full animate-spin" />
              </div>
            ) : detailPanel ? (
              <div className="p-5 space-y-4">
                {/* Header */}
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm font-medium text-white">{detailPanel.keyword}</p>
                    <p className="text-xs text-white/40">
                      Grid ({detailPanel.grid_row}, {detailPanel.grid_col}) &middot;{" "}
                      <span className="font-medium" style={{ color: scoreColor(getScore(detailPanel)) }}>
                        Score {scoreLabel(getScore(detailPanel))}
                      </span>
                      {detailPanel.rank !== null && (
                        <span className="text-emerald-400 font-medium ml-1">&middot; Rank #{detailPanel.rank}</span>
                      )}
                    </p>
                  </div>
                  <button
                    onClick={() => setDetailPanel(null)}
                    className="text-white/40 hover:text-white text-lg leading-none"
                  >
                    &times;
                  </button>
                </div>

                {/* Nearby businesses list */}
                {detailPanel.nearby_places && detailPanel.nearby_places.length > 0 ? (
                  <div className="space-y-1">
                    {(() => {
                      const seen = new Set<string>();
                      const unique = detailPanel.nearby_places.filter((p) => {
                        if (seen.has(p.place_id)) return false;
                        seen.add(p.place_id);
                        return true;
                      });
                      return (
                        <>
                    <p className="text-xs text-white/50 font-medium mb-2">
                      Nearby businesses ({unique.length})
                    </p>
                    {unique.map((place, idx) => {
                      const isUserBiz =
                        report?.place_id != null && place.place_id === report.place_id;
                      const dist =
                        place.lat != null && place.lng != null
                          ? haversineKm(detailPanel.point_lat, detailPanel.point_lng, place.lat, place.lng)
                          : null;
                      return (
                        <div
                          key={place.place_id}
                          className={`flex items-start gap-3 rounded-lg px-3 py-2.5 text-sm ${
                            isUserBiz
                              ? "bg-blue-500/15 border border-blue-500/30"
                              : "bg-white/5 border border-transparent"
                          }`}
                        >
                          <span className="text-white/40 text-xs font-mono w-5 text-right flex-shrink-0 pt-0.5">
                            {idx + 1}
                          </span>
                          <div className="min-w-0 flex-1">
                            <p className={`font-medium truncate ${isUserBiz ? "text-blue-300" : "text-white/90"}`}>
                              {place.name}
                            </p>
                            <div className="flex items-center gap-2 text-xs text-white/50 mt-0.5">
                              {place.rating != null && (
                                <span>
                                  {place.rating.toFixed(1)} ({place.user_ratings_total ?? 0})
                                </span>
                              )}
                              {dist !== null && <span>{formatDistance(dist)}</span>}
                            </div>
                            {place.vicinity && (
                              <p className="text-xs text-white/30 truncate mt-0.5">{place.vicinity}</p>
                            )}
                          </div>
                        </div>
                      );
                    })}
                        </>
                      );
                    })()}
                  </div>
                ) : (
                  <p className="text-sm text-white/40">
                    No nearby places data. Run a new analysis to populate.
                  </p>
                )}
              </div>
            ) : null}
          </aside>
        ) : (competitors.length > 0 || competitorsLoading) && (
          <aside className="w-[400px] flex-shrink-0 border-l border-white/10 overflow-y-auto bg-[#0a0a0a]">
            <div className="p-5 space-y-4">
              <div>
                <p className="text-sm font-medium text-white">Top Competitors</p>
                <p className="text-xs text-white/40">
                  {selectedKeyword === "all" ? "All keywords" : selectedKeyword}
                  {competitors.length > 0 && ` \u00b7 ${competitors.length} businesses`}
                </p>
              </div>
              {competitorsLoading ? (
                <div className="flex items-center justify-center h-40">
                  <div className="w-5 h-5 border-2 border-white/20 border-t-white/80 rounded-full animate-spin" />
                </div>
              ) : (
                <div className="space-y-1">
                  {competitors.map((comp, idx) => {
                    const isUserBiz = report?.place_id != null && comp.place_id === report.place_id;
                    const rankColor =
                      idx < 3 ? "#22c55e" : idx < 7 ? "#3b82f6" : idx < 12 ? "#f59e0b" : "#ef4444";
                    const isTracked = trackedIds.has(comp.place_id);
                    const isTracking = trackingId === comp.place_id;
                    return (
                      <div
                        key={comp.place_id}
                        className={`flex items-start gap-3 rounded-lg px-3 py-2.5 text-sm ${
                          isUserBiz
                            ? "bg-blue-500/15 border border-blue-500/30"
                            : "bg-white/5 border border-transparent"
                        }`}
                      >
                        <div className="flex items-center gap-1.5 flex-shrink-0 pt-0.5">
                          <span
                            className="inline-block w-2.5 h-2.5 rounded-full"
                            style={{ backgroundColor: rankColor }}
                          />
                          <span className="text-white/40 text-xs font-mono w-4 text-right">
                            {idx + 1}
                          </span>
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className={`font-medium truncate ${isUserBiz ? "text-blue-300" : "text-white/90"}`}>
                            {comp.name}
                          </p>
                          <div className="flex items-center gap-2 text-xs text-white/50 mt-0.5 flex-wrap">
                            <span>Avg rank {comp.avg_rank}</span>
                            <span>
                              seen in {comp.appearances}/{comp.total_points} points
                            </span>
                          </div>
                          {comp.rating != null && (
                            <div className="text-xs text-white/40 mt-0.5">
                              {comp.rating.toFixed(1)} ({comp.user_ratings_total ?? 0} reviews)
                            </div>
                          )}
                        </div>
                        {!isUserBiz && (
                          <button
                            onClick={() => handleTrackCompetitor(comp)}
                            disabled={isTracked || isTracking}
                            className={`flex-shrink-0 mt-0.5 w-6 h-6 flex items-center justify-center rounded-md text-xs transition-colors ${
                              isTracked
                                ? "bg-emerald-500/20 text-emerald-400 cursor-default"
                                : isTracking
                                ? "bg-white/5 text-white/30 cursor-wait"
                                : "bg-white/5 text-white/40 hover:bg-white/10 hover:text-white/70"
                            }`}
                            title={isTracked ? "Tracked" : "Track competitor"}
                          >
                            {isTracking ? (
                              <span className="w-3 h-3 border border-white/30 border-t-white/70 rounded-full animate-spin" />
                            ) : isTracked ? (
                              <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
                            ) : (
                              "+"
                            )}
                          </button>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </aside>
        )}
      </div>
    </div>
  );
}

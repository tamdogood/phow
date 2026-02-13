"use client";

import { useState, useEffect, useMemo, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  GoogleMap,
  useJsApiLoader,
  Marker,
  InfoWindow,
  OverlayView,
} from "@react-google-maps/api";
import { getSessionId } from "@/lib/session";
import {
  getBusinessProfile,
  createSearchGridReport,
  fetchSearchGridReport,
} from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import {
  BusinessProfile,
  SearchGridReportWithResults,
  SearchGridResult,
} from "@/types";
import { GOOGLE_MAPS_LIBRARIES, GOOGLE_MAPS_API_KEY } from "@/lib/google-maps";

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

function getRankColor(rank: number | null): string {
  if (rank === null) return "#6b7280";
  if (rank <= 3) return "#22c55e";
  if (rank <= 10) return "#f59e0b";
  return "#ef4444";
}

const GRID_SIZE_OPTIONS = [5, 7, 9, 13] as const;
const DAYS_OF_WEEK = [
  "Sunday",
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
];

const mapContainerStyle = { width: "100%", height: "100%" };
const darkMapStyles = [
  { elementType: "geometry", stylers: [{ color: "#1a1a2e" }] },
  { elementType: "labels.text.stroke", stylers: [{ color: "#1a1a2e" }] },
  { elementType: "labels.text.fill", stylers: [{ color: "#8a8a8a" }] },
  {
    featureType: "road",
    elementType: "geometry",
    stylers: [{ color: "#2a2a3e" }],
  },
  {
    featureType: "water",
    elementType: "geometry",
    stylers: [{ color: "#0e0e1a" }],
  },
  {
    featureType: "poi",
    elementType: "labels",
    stylers: [{ visibility: "off" }],
  },
];

interface CollapsibleSectionProps {
  title: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}

function CollapsibleSection({
  title,
  defaultOpen = true,
  children,
}: CollapsibleSectionProps) {
  return (
    <details open={defaultOpen} className="group border-b border-white/5">
      <summary className="flex items-center justify-between px-5 py-3 cursor-pointer select-none hover:bg-white/[0.02] transition-colors">
        <span className="text-sm font-medium text-white/80">{title}</span>
        <svg
          className="w-4 h-4 text-white/30 transition-transform group-open:rotate-180"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </summary>
      <div className="px-5 pb-4">{children}</div>
    </details>
  );
}

export default function SearchGridPage() {
  const router = useRouter();
  const { user } = useAuth();
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const [profile, setProfile] = useState<BusinessProfile | null>(null);
  const [loading, setLoading] = useState(true);

  const [reportName, setReportName] = useState("");
  const [gridSize, setGridSize] = useState<number>(7);
  const [radiusKm, setRadiusKm] = useState(5);
  const [keywordsText, setKeywordsText] = useState("");
  const [frequency, setFrequency] = useState("weekly");
  const [scheduleDay, setScheduleDay] = useState(1);
  const [scheduleHour, setScheduleHour] = useState(9);
  const [notifyEmail, setNotifyEmail] = useState("");

  const [creating, setCreating] = useState(false);
  const [report, setReport] = useState<SearchGridReportWithResults | null>(
    null
  );
  const [activeKeyword, setActiveKeyword] = useState<string | null>(null);
  const [selectedPoint, setSelectedPoint] = useState<SearchGridResult | null>(
    null
  );
  const [error, setError] = useState<string | null>(null);

  const { isLoaded } = useJsApiLoader({
    googleMapsApiKey: GOOGLE_MAPS_API_KEY,
    libraries: GOOGLE_MAPS_LIBRARIES,
  });

  const keywords = useMemo(
    () =>
      keywordsText
        .split("\n")
        .map((k) => k.trim())
        .filter(Boolean)
        .slice(0, 5),
    [keywordsText]
  );

  const centerLat = profile?.location_lat ?? 0;
  const centerLng = profile?.location_lng ?? 0;
  const hasCoords = centerLat !== 0 && centerLng !== 0;

  const gridPoints = useMemo(() => {
    if (!hasCoords) return [];
    return calculateGridPoints(centerLat, centerLng, radiusKm, gridSize);
  }, [centerLat, centerLng, radiusKm, gridSize, hasCoords]);

  const filteredResults = useMemo(() => {
    if (!report?.results) return [];
    if (!activeKeyword) return report.results;
    return report.results.filter((r) => r.keyword === activeKeyword);
  }, [report, activeKeyword]);

  const isRunning =
    report?.status === "running" || report?.latest_run?.status === "running";

  useEffect(() => {
    async function load() {
      try {
        const sessionId = getSessionId();
        const identifier = user?.id || sessionId;
        const type = user?.id ? "user" : "session";
        const bp = await getBusinessProfile(identifier, type as "session" | "user");
        if (!bp) {
          router.push("/business-setup");
          return;
        }
        setProfile(bp);
      } catch {
        setError("Failed to load business profile");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [user?.id, router]);

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const startPolling = useCallback((reportId: string) => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      try {
        const updated = await fetchSearchGridReport(reportId);
        setReport(updated);
        const stillRunning =
          updated.status === "running" ||
          updated.latest_run?.status === "running";
        if (!stillRunning && pollRef.current) {
          clearInterval(pollRef.current);
          pollRef.current = null;
        }
      } catch {
        if (pollRef.current) {
          clearInterval(pollRef.current);
          pollRef.current = null;
        }
      }
    }, 5000);
  }, []);

  const handleCreate = async () => {
    if (!profile || keywords.length === 0 || !reportName.trim()) return;
    setCreating(true);
    setError(null);
    try {
      const created = await createSearchGridReport({
        business_profile_id: profile.id,
        name: reportName.trim(),
        keywords,
        radius_km: radiusKm,
        grid_size: gridSize,
        frequency,
        schedule_day: scheduleDay,
        schedule_hour: scheduleHour,
        notify_email: notifyEmail || undefined,
      });
      const full = await fetchSearchGridReport(created.id);
      setReport(full);
      if (
        full.status === "running" ||
        full.latest_run?.status === "running"
      ) {
        startPolling(created.id);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to create report"
      );
    } finally {
      setCreating(false);
    }
  };

  const mapCenter = useMemo(
    () =>
      hasCoords ? { lat: centerLat, lng: centerLng } : { lat: 40.7, lng: -74 },
    [centerLat, centerLng, hasCoords]
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
        <div className="w-5 h-5 border-2 border-white/30 border-t-white/80 rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="h-screen bg-[#0a0a0a] flex flex-col overflow-hidden">
      <header className="dark-header flex-shrink-0 px-6 py-3 z-50 border-b border-white/5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="text-xl font-bold text-white hover:text-white/80 transition-colors tracking-tight"
            >
              PHOW
            </Link>
            <span className="hidden sm:inline-flex items-center px-2 py-0.5 rounded bg-white/10 text-[10px] font-mono text-white/60 uppercase tracking-wider">
              Dashboard
            </span>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/dashboard"
              className="px-4 py-2 text-white/70 hover:text-white text-sm font-medium transition-colors"
            >
              Dashboard
            </Link>
            <Link
              href="/community"
              className="px-4 py-2 text-white/70 hover:text-white text-sm font-medium transition-colors"
            >
              Community
            </Link>
            <Link
              href="/business-setup"
              className="px-4 py-2 text-white/70 hover:text-white text-sm font-medium transition-colors"
            >
              My Business
            </Link>
            <Link
              href="/app"
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white text-black text-sm font-medium hover:bg-white/90 transition-all"
            >
              New Analysis
            </Link>
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="w-[380px] flex-shrink-0 border-r border-white/5 overflow-y-auto bg-[#0a0a0a]">
          <div className="px-5 py-4 border-b border-white/5">
            <h2 className="text-lg font-semibold text-white">
              Local Search Grid
            </h2>
            <p className="text-white/40 text-xs mt-1">
              Track your local rankings across a geographic grid
            </p>
          </div>

          <CollapsibleSection title="Report Name">
            <input
              type="text"
              value={reportName}
              onChange={(e) => setReportName(e.target.value)}
              placeholder="e.g., Downtown Rankings"
              className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white text-sm placeholder:text-white/30 focus:outline-none focus:border-white/20"
            />
          </CollapsibleSection>

          <CollapsibleSection title="Location & Details">
            <div className="space-y-3">
              <div>
                <label className="text-xs text-white/50 block mb-1">
                  Business Name
                </label>
                <input
                  type="text"
                  value={profile?.business_name || ""}
                  readOnly
                  className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white/60 text-sm cursor-not-allowed"
                />
              </div>
              <div>
                <label className="text-xs text-white/50 block mb-1">
                  Address
                </label>
                <input
                  type="text"
                  value={profile?.location_address || ""}
                  readOnly
                  className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white/60 text-sm cursor-not-allowed"
                />
              </div>
              <Link
                href="/business-setup"
                className="inline-flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 transition-colors"
              >
                Edit business details
                <svg
                  className="w-3 h-3"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                  />
                </svg>
              </Link>
            </div>
          </CollapsibleSection>

          <CollapsibleSection title="Map Criteria">
            <div className="space-y-4">
              <div>
                <label className="text-xs text-white/50 block mb-2">
                  Grid Size
                </label>
                <div className="flex gap-2">
                  {GRID_SIZE_OPTIONS.map((size) => (
                    <button
                      key={size}
                      onClick={() => setGridSize(size)}
                      className={`flex-1 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                        gridSize === size
                          ? "bg-white text-black"
                          : "bg-white/5 text-white/60 hover:bg-white/10"
                      }`}
                    >
                      {size}x{size}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs text-white/50">Radius</label>
                  <span className="text-xs text-white/80 font-mono">
                    {radiusKm} km
                  </span>
                </div>
                <input
                  type="range"
                  min={1}
                  max={20}
                  value={radiusKm}
                  onChange={(e) => setRadiusKm(Number(e.target.value))}
                  className="w-full accent-white"
                />
              </div>
            </div>
          </CollapsibleSection>

          <CollapsibleSection title="Keywords">
            <div className="space-y-2">
              <textarea
                value={keywordsText}
                onChange={(e) => setKeywordsText(e.target.value)}
                placeholder={"coffee shop\nbest latte near me\ncafe breakfast"}
                rows={4}
                className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white text-sm placeholder:text-white/30 focus:outline-none focus:border-white/20 resize-none"
              />
              <p className="text-xs text-white/40">
                <span
                  className={
                    keywords.length >= 5 ? "text-amber-400" : "text-white/50"
                  }
                >
                  {keywords.length}/5 keywords
                </span>{" "}
                — one per line
              </p>
            </div>
          </CollapsibleSection>

          <CollapsibleSection title="Schedule" defaultOpen={false}>
            <div className="space-y-3">
              <div>
                <label className="text-xs text-white/50 block mb-1">
                  Frequency
                </label>
                <select
                  value={frequency}
                  onChange={(e) => setFrequency(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white text-sm focus:outline-none focus:border-white/20"
                >
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-white/50 block mb-1">
                  Day of Week
                </label>
                <select
                  value={scheduleDay}
                  onChange={(e) => setScheduleDay(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white text-sm focus:outline-none focus:border-white/20"
                >
                  {DAYS_OF_WEEK.map((day, i) => (
                    <option key={day} value={i}>
                      {day}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs text-white/50 block mb-1">
                  Time
                </label>
                <select
                  value={scheduleHour}
                  onChange={(e) => setScheduleHour(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white text-sm focus:outline-none focus:border-white/20"
                >
                  {Array.from({ length: 24 }, (_, h) => (
                    <option key={h} value={h}>
                      {h.toString().padStart(2, "0")}:00
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs text-white/50 block mb-1">
                  Email Notification
                </label>
                <input
                  type="email"
                  value={notifyEmail}
                  onChange={(e) => setNotifyEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white text-sm placeholder:text-white/30 focus:outline-none focus:border-white/20"
                />
              </div>
            </div>
          </CollapsibleSection>

          <div className="p-5">
            {error && (
              <p className="text-red-400 text-xs mb-3">{error}</p>
            )}
            <button
              onClick={handleCreate}
              disabled={
                creating ||
                !reportName.trim() ||
                keywords.length === 0 ||
                !profile ||
                !!report
              }
              className="w-full py-2.5 rounded-lg bg-white text-black text-sm font-semibold hover:bg-white/90 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {creating ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-black/30 border-t-black/80 rounded-full animate-spin" />
                  Creating...
                </span>
              ) : report ? (
                "Report Created"
              ) : (
                "Create Report"
              )}
            </button>
          </div>

          {isRunning && (
            <div className="px-5 pb-5">
              <div className="dark-card p-4 flex items-center gap-3">
                <div className="w-4 h-4 border-2 border-white/30 border-t-white/80 rounded-full animate-spin" />
                <div>
                  <p className="text-white text-sm font-medium">
                    Scanning grid...
                  </p>
                  <p className="text-white/40 text-xs">
                    {report?.latest_run
                      ? `${report.latest_run.points_completed}/${report.latest_run.points_total} points`
                      : "Starting..."}
                  </p>
                </div>
              </div>
            </div>
          )}

          {report && !isRunning && report.results.length > 0 && (
            <div className="px-5 pb-5">
              <div className="dark-card p-4">
                <p className="text-white text-sm font-medium mb-2">
                  Results Summary
                </p>
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div>
                    <p className="text-lg font-bold text-emerald-400">
                      {
                        report.results.filter(
                          (r) => r.rank !== null && r.rank <= 3
                        ).length
                      }
                    </p>
                    <p className="text-[10px] text-white/40">Top 3</p>
                  </div>
                  <div>
                    <p className="text-lg font-bold text-amber-400">
                      {
                        report.results.filter(
                          (r) =>
                            r.rank !== null && r.rank > 3 && r.rank <= 10
                        ).length
                      }
                    </p>
                    <p className="text-[10px] text-white/40">4-10</p>
                  </div>
                  <div>
                    <p className="text-lg font-bold text-red-400">
                      {
                        report.results.filter(
                          (r) => r.rank === null || r.rank > 10
                        ).length
                      }
                    </p>
                    <p className="text-[10px] text-white/40">11+ / N/A</p>
                  </div>
                </div>
                {report.latest_run?.avg_rank && (
                  <p className="text-white/50 text-xs mt-3 text-center">
                    Avg. rank:{" "}
                    <span className="text-white font-medium">
                      {report.latest_run.avg_rank.toFixed(1)}
                    </span>
                  </p>
                )}
              </div>
            </div>
          )}
        </aside>

        {/* Map */}
        <div className="flex-1 flex flex-col relative">
          {report && report.results.length > 0 && (
            <div className="flex-shrink-0 flex items-center gap-2 px-4 py-2 bg-[#0a0a0a] border-b border-white/5 overflow-x-auto">
              <button
                onClick={() => setActiveKeyword(null)}
                className={`px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap transition-colors ${
                  activeKeyword === null
                    ? "bg-white text-black"
                    : "bg-white/5 text-white/60 hover:bg-white/10"
                }`}
              >
                All
              </button>
              {report.keywords.map((kw) => (
                <button
                  key={kw}
                  onClick={() => setActiveKeyword(kw)}
                  className={`px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap transition-colors ${
                    activeKeyword === kw
                      ? "bg-white text-black"
                      : "bg-white/5 text-white/60 hover:bg-white/10"
                  }`}
                >
                  {kw}
                </button>
              ))}
            </div>
          )}

          <div className="flex-1">
            {isLoaded ? (
              <GoogleMap
                mapContainerStyle={mapContainerStyle}
                center={mapCenter}
                zoom={hasCoords ? 12 : 4}
                options={{
                  styles: darkMapStyles,
                  disableDefaultUI: true,
                  zoomControl: true,
                }}
              >
                {hasCoords && (
                  <Marker
                    position={{ lat: centerLat, lng: centerLng }}
                    title={profile?.business_name || "Your Business"}
                  />
                )}

                {!report &&
                  gridPoints.map((pt) => (
                    <OverlayView
                      key={`preview-${pt.row}-${pt.col}`}
                      position={{ lat: pt.lat, lng: pt.lng }}
                      mapPaneName={OverlayView.OVERLAY_MOUSE_TARGET}
                    >
                      <div
                        className="w-3 h-3 rounded-full -translate-x-1/2 -translate-y-1/2"
                        style={{ backgroundColor: "#6b7280", opacity: 0.5 }}
                      />
                    </OverlayView>
                  ))}

                {report &&
                  filteredResults.map((result, i) => (
                    <OverlayView
                      key={`result-${result.keyword}-${result.grid_row}-${result.grid_col}-${i}`}
                      position={{
                        lat: result.point_lat,
                        lng: result.point_lng,
                      }}
                      mapPaneName={OverlayView.OVERLAY_MOUSE_TARGET}
                    >
                      <div
                        className="w-6 h-6 rounded-full border-2 border-white/20 cursor-pointer flex items-center justify-center text-[9px] font-bold text-white -translate-x-1/2 -translate-y-1/2 hover:scale-125 transition-transform"
                        style={{
                          backgroundColor: getRankColor(result.rank),
                        }}
                        onClick={() => setSelectedPoint(result)}
                      >
                        {result.rank ?? "-"}
                      </div>
                    </OverlayView>
                  ))}

                {selectedPoint && (
                  <InfoWindow
                    position={{
                      lat: selectedPoint.point_lat,
                      lng: selectedPoint.point_lng,
                    }}
                    onCloseClick={() => setSelectedPoint(null)}
                  >
                    <div className="text-black p-1 min-w-[160px]">
                      <p className="font-semibold text-sm mb-1">
                        {selectedPoint.keyword}
                      </p>
                      <p className="text-xs text-gray-600">
                        Rank:{" "}
                        <span className="font-medium text-black">
                          {selectedPoint.rank ?? "Not found"}
                        </span>
                      </p>
                      {selectedPoint.top_result_name && (
                        <p className="text-xs text-gray-600 mt-0.5">
                          Top:{" "}
                          <span className="font-medium text-black">
                            {selectedPoint.top_result_name}
                          </span>
                        </p>
                      )}
                    </div>
                  </InfoWindow>
                )}
              </GoogleMap>
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="w-5 h-5 border-2 border-white/30 border-t-white/80 rounded-full animate-spin" />
              </div>
            )}
          </div>

          {!hasCoords && !loading && (
            <div className="absolute inset-0 flex items-center justify-center bg-[#0a0a0a]/80 z-10">
              <div className="text-center">
                <p className="text-white/50 text-sm mb-2">
                  No coordinates found for your business address.
                </p>
                <Link
                  href="/business-setup"
                  className="text-blue-400 hover:text-blue-300 text-sm underline"
                >
                  Update your business address
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

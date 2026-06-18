"use client";

import { Suspense, useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import { Radar as RadarIcon, RefreshCw, Settings2, ExternalLink, Check, X } from "lucide-react";
import { AppHeader } from "@/components/AppHeader";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  fetchRadarFeed,
  triggerRadarScan,
  updateRadarSubscription,
  markRadarAlert,
  severityStyle,
  relativeTime,
} from "@/lib/radar-api";
import type { RadarAlert, RadarCategory, RadarFeed } from "@/lib/radar-api";

const CATEGORIES: RadarCategory[] = [
  "competition",
  "regulation",
  "supply",
  "demand",
  "macro",
  "local",
  "reputation",
];

export default function RadarPage() {
  return (
    <Suspense
      fallback={
        <Shell>
          <div className="py-32 text-center text-white/40">Loading radar…</div>
        </Shell>
      }
    >
      <RadarPageInner />
    </Suspense>
  );
}

function RadarPageInner() {
  const bid = useSearchParams().get("bid") || "";

  const [feed, setFeed] = useState<RadarFeed | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [scanning, setScanning] = useState(false);
  const [tab, setTab] = useState<string>("all");
  const [settingsOpen, setSettingsOpen] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const load = useCallback(async () => {
    if (!bid) return;
    try {
      const data = await fetchRadarFeed(bid);
      setFeed(data);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load radar");
    } finally {
      setLoading(false);
    }
  }, [bid]);

  useEffect(() => {
    if (bid) load();
    else setLoading(false);
  }, [bid, load]);

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  async function handleScan() {
    if (!bid || scanning) return;
    setScanning(true);
    try {
      await triggerRadarScan(bid);
      toast.success("Scan started — checking the news for you…");
      pollRef.current = setInterval(async () => {
        const data = await fetchRadarFeed(bid);
        setFeed(data);
        const status = data.latest_scan?.status;
        if (status === "completed" || status === "failed") {
          if (pollRef.current) clearInterval(pollRef.current);
          pollRef.current = null;
          setScanning(false);
          toast[status === "completed" ? "success" : "error"](
            status === "completed"
              ? `Scan complete — ${data.latest_scan?.alerts_created ?? 0} new alerts`
              : "Scan failed"
          );
        }
      }, 4000);
    } catch (e) {
      setScanning(false);
      toast.error(e instanceof Error ? e.message : "Could not start scan");
    }
  }

  async function handleMark(alert: RadarAlert, action: "read" | "dismiss") {
    setFeed((f) =>
      f
        ? {
            ...f,
            alerts:
              action === "dismiss"
                ? f.alerts.filter((a) => a.id !== alert.id)
                : f.alerts.map((a) => (a.id === alert.id ? { ...a, status: "read" } : a)),
            unread_count: Math.max(0, f.unread_count - (alert.status === "new" ? 1 : 0)),
          }
        : f
    );
    try {
      await markRadarAlert(alert.id, action);
    } catch {
      /* optimistic — ignore */
    }
  }

  const alerts = feed?.alerts ?? [];
  const visible = alerts.filter((a) => {
    if (tab === "all") return true;
    if (tab === "urgent") return a.severity === "urgent";
    return a.category === tab;
  });

  if (!bid) {
    return (
      <Shell>
        <div className="text-center py-32">
          <p className="text-white/60 mb-4">Open Business Radar from your dashboard.</p>
          <Link href="/dashboard" className="text-blue-400 hover:underline text-sm">
            Go to dashboard
          </Link>
        </div>
      </Shell>
    );
  }

  return (
    <Shell>
      <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <RadarIcon className="w-6 h-6 text-blue-400" />
          <h1 className="text-2xl font-bold">Business Radar</h1>
          {feed?.unread_count ? (
            <Badge className="bg-blue-500/20 text-blue-300 border-blue-500/30">
              {feed.unread_count} new
            </Badge>
          ) : null}
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => setSettingsOpen(true)}>
            <Settings2 className="w-4 h-4 mr-1.5" /> Settings
          </Button>
          <Button size="sm" onClick={handleScan} disabled={scanning}>
            <RefreshCw className={`w-4 h-4 mr-1.5 ${scanning ? "animate-spin" : ""}`} />
            {scanning ? "Scanning…" : "Scan now"}
          </Button>
        </div>
      </div>

      {feed?.latest_scan?.completed_at && (
        <p className="text-xs text-white/40 mb-4">
          Last scan {relativeTime(feed.latest_scan.completed_at)} ·{" "}
          {feed.latest_scan.alerts_created ?? 0} alerts from{" "}
          {feed.latest_scan.candidates_found ?? 0} headlines
        </p>
      )}

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList className="flex-wrap h-auto">
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="urgent">Urgent</TabsTrigger>
          {CATEGORIES.map((c) => (
            <TabsTrigger key={c} value={c} className="capitalize">
              {c}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      <div className="mt-4 space-y-3">
        {loading ? (
          [0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-28 w-full" />)
        ) : error ? (
          <p className="text-red-400 text-sm">{error}</p>
        ) : visible.length === 0 ? (
          <div className="dark-card p-8 text-center">
            <p className="text-white/60 mb-1">No alerts here yet.</p>
            <p className="text-white/40 text-sm">
              Run a scan to monitor news that could affect your business.
            </p>
          </div>
        ) : (
          visible.map((a) => <AlertCard key={a.id} alert={a} onMark={handleMark} />)
        )}
      </div>

      {settingsOpen && feed?.subscription && (
        <SettingsDialog
          bid={bid}
          open={settingsOpen}
          onOpenChange={setSettingsOpen}
          initialTopics={feed.subscription.watch_topics ?? []}
          initialCategories={feed.subscription.categories ?? CATEGORIES}
          initialFrequency={feed.subscription.frequency ?? "daily"}
          onSaved={load}
        />
      )}
    </Shell>
  );
}

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      <AppHeader />
      <div className="pt-[72px] max-w-4xl mx-auto px-6 py-8">{children}</div>
    </div>
  );
}

function AlertCard({
  alert,
  onMark,
}: {
  alert: RadarAlert;
  onMark: (a: RadarAlert, action: "read" | "dismiss") => void;
}) {
  const s = severityStyle(alert.severity);
  const isNew = alert.status === "new";
  return (
    <div className={`dark-card p-5 ${isNew ? "border-l-2 border-l-blue-500" : ""}`}>
      <div className="flex items-center gap-2 mb-2 flex-wrap">
        <Badge className={s.badge}>{alert.severity}</Badge>
        <span className="text-xs uppercase tracking-wide text-white/40">{alert.category}</span>
        {alert.source_domain && <span className="text-xs text-white/30">· {alert.source_domain}</span>}
        <span className="text-xs text-white/30 ml-auto">
          {relativeTime(alert.published_at || alert.created_at)}
        </span>
      </div>

      <h3 className="text-white font-medium mb-1">{alert.title}</h3>
      {alert.why_it_matters && (
        <p className="text-sm text-white/70 mb-1">
          <span className="text-white/40">Why it matters: </span>
          {alert.why_it_matters}
        </p>
      )}
      {alert.suggested_action && (
        <p className="text-sm text-emerald-300/80 mb-2">→ {alert.suggested_action}</p>
      )}

      <div className="flex items-center gap-3 mt-3">
        {alert.url && (
          <a
            href={alert.url}
            target="_blank"
            rel="noreferrer"
            className="text-xs text-blue-400 hover:underline inline-flex items-center gap-1"
          >
            <ExternalLink className="w-3 h-3" /> Read source
          </a>
        )}
        {alert.status === "new" && (
          <button
            onClick={() => onMark(alert, "read")}
            className="text-xs text-white/50 hover:text-white inline-flex items-center gap-1"
          >
            <Check className="w-3 h-3" /> Mark read
          </button>
        )}
        <button
          onClick={() => onMark(alert, "dismiss")}
          className="text-xs text-white/40 hover:text-red-400 inline-flex items-center gap-1 ml-auto"
        >
          <X className="w-3 h-3" /> Dismiss
        </button>
      </div>
    </div>
  );
}

function SettingsDialog({
  bid,
  open,
  onOpenChange,
  initialTopics,
  initialCategories,
  initialFrequency,
  onSaved,
}: {
  bid: string;
  open: boolean;
  onOpenChange: (v: boolean) => void;
  initialTopics: string[];
  initialCategories: string[];
  initialFrequency: string;
  onSaved: () => void;
}) {
  const [topics, setTopics] = useState(initialTopics.join(", "));
  const [categories, setCategories] = useState<Set<string>>(new Set(initialCategories));
  const [frequency, setFrequency] = useState(initialFrequency);
  const [saving, setSaving] = useState(false);

  function toggle(cat: string) {
    setCategories((prev) => {
      const next = new Set(prev);
      if (next.has(cat)) next.delete(cat);
      else next.add(cat);
      return next;
    });
  }

  async function save() {
    setSaving(true);
    try {
      await updateRadarSubscription({
        business_profile_id: bid,
        watch_topics: topics
          .split(/[,\n]/)
          .map((t) => t.trim())
          .filter(Boolean),
        categories: Array.from(categories),
        frequency,
      });
      toast.success("Radar settings saved");
      onOpenChange(false);
      onSaved();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not save settings");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Radar settings</DialogTitle>
          <DialogDescription>
            Tune what your radar watches and how often it scans.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div>
            <label className="text-sm text-white/70 block mb-1">Watch topics</label>
            <textarea
              value={topics}
              onChange={(e) => setTopics(e.target.value)}
              rows={3}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-white/30"
              placeholder="coffee shop, Austin small business, food costs…"
            />
            <p className="text-xs text-white/30 mt-1">Comma or newline separated.</p>
          </div>

          <div>
            <label className="text-sm text-white/70 block mb-2">Categories</label>
            <div className="flex flex-wrap gap-2">
              {CATEGORIES.map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => toggle(c)}
                  className={`text-xs px-2.5 py-1 rounded-full border capitalize transition-colors ${
                    categories.has(c)
                      ? "bg-blue-500/20 text-blue-300 border-blue-500/30"
                      : "bg-white/5 text-white/40 border-white/10 hover:text-white/70"
                  }`}
                >
                  {c}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="text-sm text-white/70 block mb-1">Scan frequency</label>
            <select
              value={frequency}
              onChange={(e) => setFrequency(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-white/30"
            >
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
            </select>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" size="sm" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button size="sm" onClick={save} disabled={saving}>
            {saving ? "Saving…" : "Save"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

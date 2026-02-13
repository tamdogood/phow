"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import { getSessionId } from "@/lib/session";
import {
  fetchReviewAlertSettings,
  updateReviewAlertSettings,
  fetchReviewUsage,
  fetchReviewNotifications,
  markReviewNotificationRead,
  markAllReviewNotificationsRead,
} from "@/lib/api";
import { AlertSettings, ReviewNotification, UsageSummary } from "@/types";

const defaultSettings: AlertSettings = {
  low_rating_threshold: 2,
  instant_low_rating_enabled: true,
  daily_digest_enabled: false,
};

export default function ReputationSettingsPage() {
  const { user } = useAuth();
  const [settings, setSettings] = useState<AlertSettings>(defaultSettings);
  const [usage, setUsage] = useState<UsageSummary | null>(null);
  const [notifications, setNotifications] = useState<ReviewNotification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const actor = useMemo(() => ({ session_id: getSessionId(), user_id: user?.id }), [user?.id]);

  async function loadAll() {
    try {
      const [settingsData, usageData, notificationsData] = await Promise.all([
        fetchReviewAlertSettings(actor.session_id, actor.user_id),
        fetchReviewUsage(actor.session_id, actor.user_id),
        fetchReviewNotifications(actor.session_id, actor.user_id),
      ]);
      setSettings({
        low_rating_threshold: settingsData.low_rating_threshold,
        instant_low_rating_enabled: settingsData.instant_low_rating_enabled,
        daily_digest_enabled: settingsData.daily_digest_enabled,
      });
      setUsage(usageData);
      setNotifications(notificationsData.items);
      setUnreadCount(notificationsData.unread_count);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load settings");
    }
  }

  useEffect(() => {
    void loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id]);

  async function saveSettings() {
    setSaving(true);
    setError(null);
    try {
      const updated = await updateReviewAlertSettings(actor, settings);
      setSettings(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save settings");
    } finally {
      setSaving(false);
    }
  }

  async function markRead(notificationId: string) {
    try {
      await markReviewNotificationRead(notificationId, actor);
      await loadAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to mark notification as read");
    }
  }

  async function markAllRead() {
    try {
      await markAllReviewNotificationsRead(actor);
      await loadAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to mark all notifications as read");
    }
  }

  return (
    <main className="relative z-10 pt-24 pb-10 px-6">
      <div className="max-w-5xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-white">Reputation Settings</h1>
          <Link href="/reputation" className="text-blue-400 text-sm hover:underline">Back to Inbox</Link>
        </div>

        {error && <p className="text-red-400 text-sm mb-4">{error}</p>}

        <div className="grid lg:grid-cols-2 gap-6">
          <section className="dark-card p-4">
            <h2 className="text-white font-semibold mb-3">Alert Settings</h2>
            <div className="space-y-3">
              <label className="block text-sm text-white/80">
                Low rating threshold
                <input
                  type="number"
                  min={1}
                  max={5}
                  value={settings.low_rating_threshold}
                  onChange={(e) => setSettings((prev) => ({ ...prev, low_rating_threshold: Number(e.target.value) }))}
                  className="mt-1 w-full bg-black/30 border border-white/10 rounded p-2 text-white"
                />
              </label>

              <label className="flex items-center gap-2 text-sm text-white/80">
                <input
                  type="checkbox"
                  checked={settings.instant_low_rating_enabled}
                  onChange={(e) => setSettings((prev) => ({ ...prev, instant_low_rating_enabled: e.target.checked }))}
                />
                Instant low-rating alerts
              </label>

              <label className="flex items-center gap-2 text-sm text-white/80">
                <input
                  type="checkbox"
                  checked={settings.daily_digest_enabled}
                  onChange={(e) => setSettings((prev) => ({ ...prev, daily_digest_enabled: e.target.checked }))}
                />
                Daily digest emails
              </label>

              <button
                onClick={saveSettings}
                disabled={saving}
                className="px-3 py-2 rounded bg-emerald-500/80 text-white text-sm disabled:opacity-50"
              >
                {saving ? "Saving..." : "Save Settings"}
              </button>
            </div>
          </section>

          <section className="dark-card p-4">
            <h2 className="text-white font-semibold mb-3">Usage</h2>
            {!usage ? (
              <p className="text-white/50 text-sm">Loading usage...</p>
            ) : (
              <div className="space-y-2 text-sm text-white/80">
                <p>Plan: <span className="text-white">{usage.plan}</span></p>
                <p>Used: <span className="text-white">{usage.used}</span> / {usage.monthly_limit}</p>
                <p>Remaining: <span className="text-white">{usage.remaining}</span></p>
                <p>Status: <span className={usage.over_limit ? "text-red-400" : "text-emerald-400"}>{usage.over_limit ? "Over limit" : "Within limit"}</span></p>
              </div>
            )}
          </section>

          <section className="dark-card p-4 lg:col-span-2">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-white font-semibold">Notifications ({unreadCount} unread)</h2>
              <button onClick={markAllRead} className="text-xs text-blue-400 hover:underline">Mark all read</button>
            </div>
            {notifications.length === 0 ? (
              <p className="text-white/50 text-sm">No notifications yet.</p>
            ) : (
              <div className="space-y-2">
                {notifications.map((note) => (
                  <div key={note.id} className={`rounded border p-3 ${note.is_read ? "border-white/10" : "border-blue-400/50"}`}>
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-white text-sm font-medium">{note.title}</p>
                        <p className="text-white/70 text-sm">{note.body}</p>
                        <p className="text-white/40 text-xs mt-1">{new Date(note.created_at).toLocaleString()}</p>
                      </div>
                      {!note.is_read && (
                        <button onClick={() => markRead(note.id)} className="text-xs text-blue-400 hover:underline">Read</button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}

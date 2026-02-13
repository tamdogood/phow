"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { getSessionId } from "@/lib/session";
import {
  fetchReviewConnections,
  startReviewConnection,
  disconnectReviewConnection,
  callbackReviewConnection,
} from "@/lib/api";
import { ReviewConnection } from "@/types";

export default function ReputationConnectionsPage() {
  const { user } = useAuth();
  const searchParams = useSearchParams();
  const [connections, setConnections] = useState<ReviewConnection[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loadingSource, setLoadingSource] = useState<string | null>(null);

  const actor = { session_id: getSessionId(), user_id: user?.id };

  async function load() {
    try {
      const data = await fetchReviewConnections(actor.session_id, actor.user_id);
      setConnections(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load connections");
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id]);

  useEffect(() => {
    async function handleCallback() {
      const code = searchParams.get("code");
      const state = searchParams.get("state") || undefined;
      if (!code) return;
      try {
        await callbackReviewConnection("google", actor, code, state);
        await load();
      } catch (err) {
        setError(err instanceof Error ? err.message : "OAuth callback failed");
      }
    }
    void handleCallback();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams, user?.id]);

  async function connect(source: "google" | "yelp" | "meta") {
    setLoadingSource(source);
    setError(null);
    try {
      const result = await startReviewConnection(source, actor);
      if (source === "google" && typeof result.authorization_url === "string") {
        window.location.href = result.authorization_url;
        return;
      }
      if (source === "yelp" && typeof result.deeplink === "string") {
        window.open(result.deeplink, "_blank");
      }
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to connect");
    } finally {
      setLoadingSource(null);
    }
  }

  async function disconnect(source: "google" | "yelp" | "meta") {
    setLoadingSource(source);
    setError(null);
    try {
      await disconnectReviewConnection(source, actor);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to disconnect");
    } finally {
      setLoadingSource(null);
    }
  }

  return (
    <main className="relative z-10 pt-24 pb-10 px-6">
      <div className="max-w-5xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-white">Connections</h1>
          <Link href="/reputation" className="text-blue-400 text-sm hover:underline">Back to Inbox</Link>
        </div>

        {error && <p className="text-red-400 text-sm mb-4">{error}</p>}

        <div className="grid md:grid-cols-3 gap-4">
          {connections.map((connection) => {
            const connected = connection.status === "connected";
            const source = connection.source as "google" | "yelp" | "meta";
            return (
              <div key={connection.source} className="dark-card p-4">
                <h2 className="text-white font-semibold capitalize mb-1">{connection.source}</h2>
                <p className="text-white/60 text-sm mb-2">Status: {connection.status}</p>
                <p className="text-white/50 text-xs mb-3">
                  Last sync: {connection.last_synced_at ? new Date(connection.last_synced_at).toLocaleString() : "Never"}
                </p>
                {connected ? (
                  <button
                    onClick={() => disconnect(source)}
                    disabled={loadingSource === source}
                    className="px-3 py-2 rounded bg-red-500/80 text-white text-sm disabled:opacity-50"
                  >
                    {loadingSource === source ? "Working..." : "Disconnect"}
                  </button>
                ) : (
                  <button
                    onClick={() => connect(source)}
                    disabled={loadingSource === source}
                    className="px-3 py-2 rounded bg-emerald-500/80 text-white text-sm disabled:opacity-50"
                  >
                    {loadingSource === source ? "Working..." : "Connect"}
                  </button>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </main>
  );
}

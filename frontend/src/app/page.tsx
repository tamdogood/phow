"use client";

import { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";

const Chat = dynamic(() => import("@/components/chat").then((mod) => ({ default: mod.Chat })), {
  ssr: false,
});

const ToolSelector = dynamic(
  () => import("@/components/chat/ToolSelector").then((mod) => ({ default: mod.ToolSelector })),
  { ssr: false }
);

interface Tool {
  id: string;
  name: string;
  description: string;
  icon: string;
  hints?: string[];
  capabilities?: string[];
}

export default function Home() {
  const { user, loading: authLoading, isConfigured, signInWithGoogle } = useAuth();
  const [selectedTool, setSelectedTool] = useState<Tool | null>(null);
  const [tools, setTools] = useState<Tool[]>([]);
  const [chatKey, setChatKey] = useState(0);

  // Fetch tools on mount
  useEffect(() => {
    async function fetchTools() {
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/tools`
        );
        if (response.ok) {
          const data = await response.json();
          setTools(data);
        }
      } catch (error) {
        console.error("Failed to fetch tools:", error);
      }
    }
    fetchTools();
  }, []);

  const handleSelectTool = (toolId: string) => {
    const tool = tools.find((t) => t.id === toolId);
    if (tool) {
      setSelectedTool(tool);
      setChatKey((prev) => prev + 1);
    }
  };

  const handleSwitchTool = (toolId: string) => {
    const tool = tools.find((t) => t.id === toolId);
    if (tool) {
      setSelectedTool(tool);
      setChatKey((prev) => prev + 1);
    }
  };

  const handleReset = () => {
    setSelectedTool(null);
    setChatKey((prev) => prev + 1);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Background Image Overlay */}
      <div
        className="absolute inset-0 z-0"
        style={{
          backgroundImage: `url('https://plus.unsplash.com/premium_photo-1664443577580-dd2674e9d359?q=80&w=2071&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D')`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat',
        }}
      />
      {/* Gradient Overlay for depth */}
      <div className="absolute inset-0 z-0 bg-gradient-to-b from-slate-900/40 via-transparent to-slate-900/60" />

      {/* Header */}
      <header className="glass-header fixed top-0 left-0 right-0 z-50 px-6 py-4">
        <div className="mx-auto max-w-6xl flex items-center justify-between">
          <button
            type="button"
            onClick={handleReset}
            className="text-left text-xl font-bold text-white hover:text-white/80 transition-colors cursor-pointer flex items-center gap-2"
            aria-label="Go to home and clear chat"
          >
            <span className="text-2xl">PHOW</span>
          </button>
          <div className="flex items-center gap-3">
            {!authLoading && (
              <>
                {user ? (
                  <>
                    <Link
                      href="/dashboard"
                      className="px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white text-sm font-medium transition-all border border-white/20"
                    >
                      Dashboard
                    </Link>
                    <Link
                      href="/business-setup"
                      className="px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white text-sm font-medium transition-all border border-white/20"
                    >
                      My Business
                    </Link>
                    <Link
                      href="/profile"
                      className="px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white text-sm font-medium transition-all border border-white/20 flex items-center gap-2"
                    >
                      <span className="truncate max-w-[120px]">
                        {user.user_metadata?.full_name || user.email?.split("@")[0]}
                      </span>
                    </Link>
                  </>
                ) : (
                  <>
                    <Link
                      href="/dashboard"
                      className="px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white text-sm font-medium transition-all border border-white/20"
                    >
                      Dashboard
                    </Link>
                    <Link
                      href="/business-setup"
                      className="px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white text-sm font-medium transition-all border border-white/20"
                    >
                      Business Setup
                    </Link>
                    <button
                      onClick={signInWithGoogle}
                      disabled={!isConfigured}
                      className="px-4 py-2 rounded-lg bg-white text-slate-900 text-sm font-medium hover:bg-white/90 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                      title={!isConfigured ? "Supabase not configured" : undefined}
                    >
                      Sign In
                    </button>
                  </>
                )}
              </>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative z-10 pt-20">
        {!selectedTool ? (
          <div className="flex flex-col items-center justify-center min-h-[calc(100vh-80px)] px-6">
            {/* Hero Section */}
            <div className="text-center mb-12 mt-8">
              <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold text-white mb-6 tracking-tight">
                AI-Powered Business
                <br />
                <span className="text-gradient">Analytics</span>
              </h1>
              <p className="text-lg md:text-xl text-white/70 max-w-2xl mx-auto">
                Get insights for your small business by chatting with AI.
                <br className="hidden md:block" />
                Location analysis, market validation, and competitive intelligence.
              </p>
            </div>

            {/* Tool Selector */}
            <div className="w-full max-w-4xl">
              <ToolSelector onSelectTool={handleSelectTool} />
            </div>

            {/* Footer tagline */}
            <p className="text-white/40 text-sm mt-12 mb-8">
              Trusted by small business owners everywhere
            </p>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto min-h-[calc(100vh-80px)]">
            <Chat
              key={chatKey}
              toolId={selectedTool.id}
              toolName={selectedTool.name}
              toolDescription={selectedTool.description}
              toolIcon={selectedTool.icon}
              toolHints={selectedTool.hints}
              toolCapabilities={selectedTool.capabilities}
              onSwitchTool={handleSwitchTool}
            />
          </div>
        )}
      </main>
    </div>
  );
}

"use client";

import dynamic from "next/dynamic";
import { useIntersectionObserver } from "@/hooks/useIntersectionObserver";

const HeroMapDemo = dynamic(
  () => import("./HeroMapDemo").then((mod) => mod.HeroMapDemo),
  {
    ssr: false,
    loading: () => <div className="w-full h-full bg-[#111] animate-pulse" />,
  }
);

export function DemoSection() {
  const { ref, isVisible } = useIntersectionObserver<HTMLElement>({ threshold: 0.1 });

  return (
    <section id="demo" ref={ref} className="relative py-16 px-6">
      <div className="mx-auto max-w-6xl">
        <div className="relative">
          {/* Browser mockup frame */}
          <div
            className={`rounded-xl overflow-hidden border border-white/10 bg-[#111] shadow-2xl shadow-black/50 animate-on-scroll ${isVisible ? "visible" : ""}`}
          >
            {/* Browser chrome */}
            <div className="flex items-center gap-2 px-4 py-3 bg-[#1a1a1a] border-b border-white/10">
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-[#ff5f57]" />
                <div className="w-3 h-3 rounded-full bg-[#febc2e]" />
                <div className="w-3 h-3 rounded-full bg-[#28c840]" />
              </div>
              <div className="flex-1 mx-4">
                <div className="bg-[#0a0a0a] rounded px-3 py-1.5 text-sm text-white/50 font-mono max-w-xs mx-auto text-center">
                  phow.ai/app
                </div>
              </div>
              <div className="w-[52px]" />
            </div>
            {/* Map content */}
            <div className="h-[400px] md:h-[500px] relative">
              <HeroMapDemo />

              {/* Floating Widgets */}
              {/* Location Score Widget - Top Left */}
              <div
                className={`absolute top-4 left-4 bg-[#0a0a0a]/95 backdrop-blur-sm border border-white/10 rounded-xl p-4 w-48 animate-slide-in-left ${isVisible ? "" : "opacity-0"}`}
                style={{ animationDelay: "0.3s" }}
              >
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center">
                    <span className="text-blue-400 text-sm">📍</span>
                  </div>
                  <span className="text-white/70 text-sm font-medium">Location Score</span>
                </div>
                <div className="flex items-end gap-2">
                  <span className="text-4xl font-bold text-white">87</span>
                  <span className="text-green-400 text-sm mb-1">+12%</span>
                </div>
                <div className="mt-2 h-1.5 bg-white/10 rounded-full overflow-hidden">
                  <div className="h-full w-[87%] bg-gradient-to-r from-blue-500 to-blue-400 rounded-full" />
                </div>
              </div>

              {/* Competitors Widget - Top Right */}
              <div
                className={`absolute top-4 right-4 bg-[#0a0a0a]/95 backdrop-blur-sm border border-white/10 rounded-xl p-4 w-52 animate-slide-in-right ${isVisible ? "" : "opacity-0"}`}
                style={{ animationDelay: "0.4s" }}
              >
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-8 h-8 rounded-lg bg-orange-500/20 flex items-center justify-center">
                    <span className="text-orange-400 text-sm">🎯</span>
                  </div>
                  <span className="text-white/70 text-sm font-medium">Competitors</span>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-white/60 text-xs">Within 0.5mi</span>
                    <span className="text-white font-semibold">12</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-white/60 text-xs">Avg Rating</span>
                    <span className="text-amber-400 font-semibold flex items-center gap-1">
                      <span>4.2</span>
                      <span className="text-xs">★</span>
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-white/60 text-xs">Price Level</span>
                    <span className="text-green-400 font-semibold">$$</span>
                  </div>
                </div>
              </div>

              {/* Transit Score Widget - Bottom Left */}
              <div
                className={`absolute bottom-4 left-4 bg-[#0a0a0a]/95 backdrop-blur-sm border border-white/10 rounded-xl p-4 w-48 animate-slide-in-left ${isVisible ? "" : "opacity-0"}`}
                style={{ animationDelay: "0.5s" }}
              >
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-8 h-8 rounded-lg bg-green-500/20 flex items-center justify-center">
                    <span className="text-green-400 text-sm">🚇</span>
                  </div>
                  <span className="text-white/70 text-sm font-medium">Transit Access</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-3xl font-bold text-green-400">A+</span>
                  <div className="text-xs text-white/50">
                    <div>2 BART stations</div>
                    <div>5 bus lines</div>
                  </div>
                </div>
              </div>

              {/* Demographics Widget - Bottom Right */}
              <div
                className={`absolute bottom-4 right-4 bg-[#0a0a0a]/95 backdrop-blur-sm border border-white/10 rounded-xl p-4 w-52 animate-slide-in-right ${isVisible ? "" : "opacity-0"}`}
                style={{ animationDelay: "0.6s" }}
              >
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-8 h-8 rounded-lg bg-purple-500/20 flex items-center justify-center">
                    <span className="text-purple-400 text-sm">👥</span>
                  </div>
                  <span className="text-white/70 text-sm font-medium">Demographics</span>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-white/60 text-xs">Foot Traffic</span>
                    <span className="text-white font-semibold">High</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-white/60 text-xs">Median Income</span>
                    <span className="text-white font-semibold">$95K</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-white/60 text-xs">Age Group</span>
                    <span className="text-white font-semibold">25-44</span>
                  </div>
                </div>
              </div>

              {/* AI Insight Banner */}
              <div
                className={`absolute bottom-20 left-1/2 -translate-x-1/2 bg-gradient-to-r from-blue-600/90 to-purple-600/90 backdrop-blur-sm border border-white/20 rounded-full px-4 py-2 animate-fade-in-up ${isVisible ? "" : "opacity-0"}`}
                style={{ animationDelay: "0.7s" }}
              >
                <div className="flex items-center gap-2">
                  <span className="animate-pulse">✨</span>
                  <span className="text-white text-sm font-medium">
                    AI: This location scores 23% above area average
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Caption */}
        <p className="text-center text-white/40 text-sm mt-6 font-mono">
          Location Scout — Analyze any address with AI-powered insights
        </p>
      </div>
    </section>
  );
}

"use client";

import Link from "next/link";
import dynamic from "next/dynamic";

const HeroMapDemo = dynamic(() => import("./HeroMapDemo").then((mod) => mod.HeroMapDemo), {
  ssr: false,
  loading: () => (
    <div className="absolute inset-0 bg-slate-900" />
  ),
});

export function HeroSection() {
  return (
    <section className="relative min-h-screen flex items-center px-6 pt-20 overflow-hidden">
      {/* Map as full background */}
      <div className="absolute inset-0 z-0">
        <HeroMapDemo />
      </div>

      {/* Gradient overlay - right side for text readability */}
      <div className="absolute inset-0 z-[1] bg-gradient-to-l from-slate-900/80 via-slate-900/40 to-transparent" />

      {/* Bottom fade - gradual transition to page background */}
      <div
        className="absolute bottom-0 left-0 right-0 h-48 z-[1]"
        style={{
          background: "linear-gradient(to bottom, transparent 0%, rgba(15, 23, 42, 0.5) 30%, rgba(15, 23, 42, 0.8) 60%, rgba(15, 23, 42, 0.95) 100%)"
        }}
      />

      <div className="relative z-10 mx-auto max-w-6xl w-full flex justify-end">
        <div className="max-w-xl text-right">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/10 border border-white/20 mb-6 animate-fade-in-up">
            <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
            <span className="text-sm text-white/80">Now in public beta</span>
          </div>

          {/* Main Headline */}
          <h1
            className="text-4xl md:text-5xl font-bold text-white mb-4 tracking-tight animate-fade-in-up"
            style={{ animationDelay: "0.1s", textShadow: "0 2px 20px rgba(0,0,0,0.8)" }}
          >
            AI-Powered Analytics
            <br />
            <span className="text-gradient">for Small Business</span>
          </h1>

          {/* Subheadline */}
          <p
            className="text-base text-white/90 mb-6 animate-fade-in-up"
            style={{ animationDelay: "0.2s", textShadow: "0 1px 10px rgba(0,0,0,0.8)" }}
          >
            Location analysis, market validation, and competitive intelligence—powered by AI.
          </p>

          {/* CTAs */}
          <div className="flex flex-wrap gap-3 mb-8 justify-end animate-fade-in-up" style={{ animationDelay: "0.3s" }}>
            <Link
              href="/app"
              className="px-6 py-3 rounded-lg bg-gradient-to-r from-sky-500 to-blue-600 text-white font-semibold hover:from-sky-400 hover:to-blue-500 transition-all shadow-lg shadow-sky-500/25"
            >
              Get Started Free
            </Link>
            <Link
              href="/features"
              className="px-6 py-3 rounded-lg bg-white/10 text-white font-semibold hover:bg-white/20 transition-all border border-white/20 backdrop-blur-sm"
            >
              See How It Works
            </Link>
          </div>

          {/* Stats row */}
          <div className="flex flex-wrap gap-4 justify-end animate-fade-in-up" style={{ animationDelay: "0.4s" }}>
            <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-900/60 backdrop-blur-sm border border-white/10">
              <span className="text-xl font-bold text-sky-400">87</span>
              <span className="text-xs text-white/60">Location Score</span>
            </div>
            <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-900/60 backdrop-blur-sm border border-white/10">
              <span className="text-xl font-bold text-orange-400">12</span>
              <span className="text-xs text-white/60">Competitors</span>
            </div>
            <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-900/60 backdrop-blur-sm border border-white/10">
              <span className="text-xl font-bold text-green-400">A+</span>
              <span className="text-xs text-white/60">Transit</span>
            </div>
          </div>

          {/* Trust Indicators */}
          <div className="mt-6 flex flex-wrap items-center gap-4 justify-end text-white/50 text-xs animate-fade-in-up" style={{ animationDelay: "0.5s" }}>
            <span>No credit card required</span>
            <span className="w-1 h-1 rounded-full bg-white/30" />
            <span>Free to start</span>
            <span className="w-1 h-1 rounded-full bg-white/30" />
            <span>Cancel anytime</span>
          </div>
        </div>
      </div>

      {/* Scroll indicator */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce z-10">
        <svg className="w-6 h-6 text-white/40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
        </svg>
      </div>
    </section>
  );
}

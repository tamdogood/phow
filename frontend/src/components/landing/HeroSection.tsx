"use client";

import Link from "next/link";

export function HeroSection() {
  return (
    <section className="relative min-h-screen flex items-center justify-center px-6 pt-20 hero-gradient">
      <div className="mx-auto max-w-5xl text-center">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 border border-white/20 mb-8 animate-fade-in-up">
          <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
          <span className="text-sm text-white/80">Now in public beta</span>
        </div>

        {/* Main Headline */}
        <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold text-white mb-6 tracking-tight animate-fade-in-up" style={{ animationDelay: "0.1s" }}>
          AI-Powered Analytics
          <br />
          <span className="text-gradient">for Your Small Business</span>
        </h1>

        {/* Subheadline */}
        <p className="text-lg md:text-xl text-white/70 max-w-2xl mx-auto mb-10 animate-fade-in-up" style={{ animationDelay: "0.2s" }}>
          Make smarter decisions with AI-driven insights. Location analysis, market validation,
          and competitive intelligence—all in one platform.
        </p>

        {/* CTAs */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center animate-fade-in-up" style={{ animationDelay: "0.3s" }}>
          <Link
            href="/app"
            className="px-8 py-4 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 text-white font-semibold text-lg hover:from-sky-400 hover:to-blue-500 transition-all shadow-lg shadow-sky-500/25 animate-glow-pulse"
          >
            Get Started Free
          </Link>
          <Link
            href="/features"
            className="px-8 py-4 rounded-xl bg-white/10 text-white font-semibold text-lg hover:bg-white/20 transition-all border border-white/20"
          >
            See How It Works
          </Link>
        </div>

        {/* Trust Indicators */}
        <div className="mt-16 animate-fade-in-up" style={{ animationDelay: "0.4s" }}>
          <p className="text-sm text-white/40 mb-4">Trusted by small business owners</p>
          <div className="flex justify-center items-center gap-8 text-white/30">
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span className="text-sm">No credit card required</span>
            </div>
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span className="text-sm">Free to start</span>
            </div>
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span className="text-sm">Cancel anytime</span>
            </div>
          </div>
        </div>

        {/* Floating Product Preview */}
        <div className="mt-16 relative animate-fade-in-up" style={{ animationDelay: "0.5s" }}>
          <div className="glass-card p-4 max-w-3xl mx-auto animate-float">
            <div className="bg-slate-900/50 rounded-lg p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-3 h-3 rounded-full bg-red-500" />
                <div className="w-3 h-3 rounded-full bg-yellow-500" />
                <div className="w-3 h-3 rounded-full bg-green-500" />
                <span className="text-xs text-white/40 ml-2">PHOW Analytics</span>
              </div>
              <div className="flex gap-4">
                <div className="flex-1 bg-white/5 rounded-lg p-4">
                  <div className="text-2xl mb-2">📍</div>
                  <h4 className="text-white font-medium text-sm">Location Score</h4>
                  <p className="text-3xl font-bold text-sky-400 mt-2">87/100</p>
                </div>
                <div className="flex-1 bg-white/5 rounded-lg p-4">
                  <div className="text-2xl mb-2">📊</div>
                  <h4 className="text-white font-medium text-sm">Market Potential</h4>
                  <p className="text-3xl font-bold text-violet-400 mt-2">High</p>
                </div>
                <div className="flex-1 bg-white/5 rounded-lg p-4">
                  <div className="text-2xl mb-2">🎯</div>
                  <h4 className="text-white font-medium text-sm">Competitors</h4>
                  <p className="text-3xl font-bold text-orange-400 mt-2">12</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Scroll indicator */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
        <svg className="w-6 h-6 text-white/40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
        </svg>
      </div>
    </section>
  );
}

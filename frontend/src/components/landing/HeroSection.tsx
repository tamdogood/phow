"use client";

import Link from "next/link";

export function HeroSection() {
  return (
    <section className="relative min-h-screen flex items-center justify-center px-6 pt-20">
      <div className="relative z-10 max-w-4xl text-center">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#1a1a1a] border border-white/10 mb-8 animate-fade-in-up">
          <span className="text-sm">📍</span>
          <span className="text-xs font-mono text-white/70 uppercase tracking-wider">PHOW</span>
        </div>

        {/* Main Headline */}
        <h1
          className="text-5xl md:text-7xl font-bold text-white mb-6 tracking-tight animate-fade-in-up"
          style={{ animationDelay: "0.1s" }}
        >
          AI-Powered Analytics
          <br />
          for Small <span className="text-accent-blue">Business</span>
        </h1>

        {/* Subtitle */}
        <p
          className="text-lg md:text-xl text-white/50 max-w-2xl mx-auto mb-10 animate-fade-in-up"
          style={{ animationDelay: "0.2s" }}
        >
          Location analysis, market validation, and competitive
          intelligence—powered by AI.
        </p>

        {/* CTAs */}
        <div
          className="flex flex-wrap gap-4 justify-center mb-8 animate-fade-in-up"
          style={{ animationDelay: "0.3s" }}
        >
          <Link
            href="/app"
            className="inline-flex items-center gap-2 px-6 py-3.5 rounded-lg bg-white text-black font-semibold hover:bg-white/90 transition-all"
          >
            Get Started Free
            <span className="px-2 py-0.5 rounded bg-black/10 text-xs font-mono">FREE</span>
          </Link>
        </div>

        {/* Monospace Tagline */}
        <p
          className="font-mono text-sm md:text-base text-white/40 tracking-wider mb-10 animate-fade-in-up"
          style={{ animationDelay: "0.4s" }}
        >
          Free forever. No credit card. Built for small business owners.
        </p>

        {/* Trust Indicators */}
        <div
          className="flex flex-wrap items-center justify-center gap-6 md:gap-8 animate-fade-in-up"
          style={{ animationDelay: "0.5s" }}
        >
          <div className="flex items-center gap-2 text-white/50">
            <svg className="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
            <span className="font-mono text-xs uppercase tracking-widest">AI-Powered</span>
          </div>
          <div className="flex items-center gap-2 text-white/50">
            <svg className="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
            <span className="font-mono text-xs uppercase tracking-widest">Real-Time Data</span>
          </div>
          <div className="flex items-center gap-2 text-white/50">
            <svg className="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
            <span className="font-mono text-xs uppercase tracking-widest">Free to Start</span>
          </div>
        </div>
      </div>

      {/* Scroll indicator */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce z-10">
        <svg className="w-6 h-6 text-white/30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
        </svg>
      </div>
    </section>
  );
}

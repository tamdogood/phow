"use client";

import Link from "next/link";
import { useIntersectionObserver } from "@/hooks/useIntersectionObserver";

export function CTASection() {
  const { ref, isVisible } = useIntersectionObserver<HTMLElement>({ threshold: 0.1 });

  return (
    <section ref={ref} className="relative z-10 py-24 px-6">
      <div className="mx-auto max-w-4xl">
        <div
          className={`rounded-2xl p-12 md:p-16 text-center bg-[#111] border border-white/5 animate-on-scroll ${isVisible ? "visible" : ""}`}
        >
          {/* Headline */}
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Ready to grow your <span className="text-accent-blue">business</span>?
          </h2>
          <p className="text-lg text-white/50 max-w-xl mx-auto mb-8">
            Join small business owners making smarter decisions with AI-powered analytics.
          </p>

          {/* CTA */}
          <Link
            href="/app"
            className="inline-flex items-center gap-2 px-8 py-4 rounded-lg bg-white text-black font-semibold text-lg hover:bg-white/90 transition-all"
          >
            Get Started Free
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </Link>

          {/* Trust line */}
          <p className="mt-6 text-sm text-white/40 font-mono">
            No credit card required
          </p>
        </div>
      </div>
    </section>
  );
}

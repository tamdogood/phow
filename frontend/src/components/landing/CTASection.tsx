"use client";

import Link from "next/link";
import { useIntersectionObserver } from "@/hooks/useIntersectionObserver";

export function CTASection() {
  const { ref, isVisible } = useIntersectionObserver<HTMLElement>({ threshold: 0.1 });

  return (
    <section ref={ref} className="relative z-10 py-24 px-6">
      <div className="mx-auto max-w-4xl">
        <div
          className={`rounded-2xl p-12 md:p-16 text-center bg-gray-50 border border-gray-100 animate-on-scroll ${isVisible ? "visible" : ""}`}
        >
          {/* Headline */}
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
            Ready to grow your <span className="text-blue-600">business</span>?
          </h2>
          <p className="text-lg text-gray-500 max-w-xl mx-auto mb-8">
            Join small business owners making smarter decisions with AI-powered analytics.
          </p>

          {/* CTA */}
          <Link
            href="/app"
            className="inline-flex items-center gap-2 px-8 py-4 rounded-lg bg-gray-900 text-white font-semibold text-lg hover:bg-gray-800 transition-all shadow-lg hover:shadow-xl"
          >
            Get Started Free
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </Link>

          {/* Trust line */}
          <p className="mt-6 text-sm text-gray-400 font-mono">
            No credit card required
          </p>
        </div>
      </div>
    </section>
  );
}

"use client";

import Link from "next/link";
import { useIntersectionObserver } from "@/hooks/useIntersectionObserver";

export function CTASection() {
  const { ref, isVisible } = useIntersectionObserver<HTMLElement>({ threshold: 0.1 });

  return (
    <section ref={ref} className="relative z-10 py-24 px-6">
      <div className="mx-auto max-w-4xl">
        <div className={`glass-card p-12 md:p-16 text-center relative overflow-hidden animate-on-scroll ${isVisible ? "visible" : ""}`}>
          {/* Background Glow */}
          <div className="absolute inset-0 bg-gradient-to-br from-sky-500/10 via-transparent to-violet-500/10 pointer-events-none" />

          {/* Content */}
          <div className="relative">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Ready to Transform Your Business?
            </h2>
            <p className="text-lg text-white/60 max-w-xl mx-auto mb-8">
              Join thousands of small business owners making smarter decisions with AI-powered analytics.
            </p>

            {/* CTA */}
            <Link
              href="/app"
              className="inline-flex px-10 py-5 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 text-white font-semibold text-lg hover:from-sky-400 hover:to-blue-500 transition-all shadow-lg shadow-sky-500/25 animate-glow-pulse"
            >
              Get Started Free
            </Link>

            {/* Stats */}
            <div className="mt-12 grid grid-cols-3 gap-8 max-w-md mx-auto">
              <div>
                <p className="text-2xl md:text-3xl font-bold text-white">1K+</p>
                <p className="text-sm text-white/50">Users</p>
              </div>
              <div>
                <p className="text-2xl md:text-3xl font-bold text-white">10K+</p>
                <p className="text-sm text-white/50">Analyses</p>
              </div>
              <div>
                <p className="text-2xl md:text-3xl font-bold text-white">4.9</p>
                <p className="text-sm text-white/50">Rating</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

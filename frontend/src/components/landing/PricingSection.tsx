"use client";

import Link from "next/link";
import { useIntersectionObserver } from "@/hooks/useIntersectionObserver";

const benefits = [
  { text: "Access to all AI tools", included: true },
  { text: "Unlimited conversations", included: true },
  { text: "Location analysis reports", included: true },
  { text: "Market validation insights", included: true },
  { text: "Competitor research", included: true },
  { text: "Export reports (PDF)", included: true },
];

export function PricingSection() {
  const { ref, isVisible } = useIntersectionObserver<HTMLElement>({ threshold: 0.1 });

  return (
    <section ref={ref} className="relative z-10 py-24 px-6 bg-slate-900/30">
      <div className="mx-auto max-w-4xl">
        {/* Section Header */}
        <div className={`text-center mb-12 animate-on-scroll ${isVisible ? "visible" : ""}`}>
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Free to Start
          </h2>
          <p className="text-lg text-white/60 max-w-2xl mx-auto">
            No credit card required. Start using PHOW today and upgrade when you&apos;re ready.
          </p>
        </div>

        {/* Pricing Card */}
        <div className={`glass-card p-8 md:p-12 max-w-lg mx-auto text-center animate-on-scroll ${isVisible ? "visible" : ""}`} style={{ transitionDelay: "150ms" }}>
          {/* Price */}
          <div className="mb-8">
            <div className="inline-flex items-baseline gap-1">
              <span className="text-5xl font-bold text-white">$0</span>
              <span className="text-white/60">/month</span>
            </div>
            <p className="text-sky-400 mt-2 text-sm font-medium">Free during beta</p>
          </div>

          {/* Benefits */}
          <ul className="space-y-4 mb-8 text-left">
            {benefits.map((benefit) => (
              <li key={benefit.text} className="flex items-center gap-3">
                <svg className="w-5 h-5 text-green-400 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span className="text-white/80">{benefit.text}</span>
              </li>
            ))}
          </ul>

          {/* CTA */}
          <Link
            href="/app"
            className="block w-full px-8 py-4 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 text-white font-semibold text-lg hover:from-sky-400 hover:to-blue-500 transition-all shadow-lg shadow-sky-500/25"
          >
            Get Started Free
          </Link>

          {/* Trust */}
          <p className="text-white/40 text-sm mt-4">
            No credit card required • Cancel anytime
          </p>
        </div>
      </div>
    </section>
  );
}

"use client";

import Link from "next/link";
import { Check } from "lucide-react";
import { Reveal } from "./Reveal";

interface Plan {
  name: string;
  price: string;
  cadence: string;
  blurb: string;
  features: string[];
  cta: string;
  featured?: boolean;
}

const PLANS: Plan[] = [
  {
    name: "Starter",
    price: "$0",
    cadence: "/ month",
    blurb: "Get your bearings.",
    cta: "Start free",
    features: [
      "1 storefront",
      "Weekly Daily Brief",
      "Weekly Radar scan",
      "3 tracked competitors",
      "1 Feasibility Study",
    ],
  },
  {
    name: "Pro",
    price: "$49",
    cadence: "/ month",
    blurb: "The full watchtower.",
    cta: "Go Pro",
    featured: true,
    features: [
      "Everything in Starter",
      "Daily Brief + daily Radar",
      "15 tracked competitors",
      "Unlimited studies + what-if scenarios",
      "Reputation Hub & reply drafts",
      "Email digest + PDF export",
    ],
  },
  {
    name: "Multi-unit",
    price: "$149",
    cadence: "/ month",
    blurb: "For groups & franchises.",
    cta: "Choose Multi",
    features: [
      "Everything in Pro",
      "Multiple locations",
      "Cross-location brief",
      "Priority data refresh",
      "API access",
    ],
  },
];

export function PricingSection() {
  return (
    <section id="pricing" className="px-6 py-20 lg:py-28 border-t border-[#141414] scroll-mt-24">
      <div className="mx-auto max-w-[1200px]">
        <Reveal className="max-w-2xl mx-auto text-center">
          <p className="font-mono text-[12px] tracking-[0.12em] text-[#a7a7a7] uppercase">
            Pricing
          </p>
          <h2 className="mt-5 text-[32px] sm:text-[40px] font-medium leading-[1.12] tracking-[-0.025em] text-white">
            Priced like a coffee, not a consultant
          </h2>
          <p className="mt-5 text-[16px] leading-[1.6] text-[#a7a7a7]">
            Anchor on value, not cost. Every plan is free during beta — start today, upgrade
            when it pays for itself.
          </p>
        </Reveal>

        <div className="mt-14 grid md:grid-cols-3 gap-5 items-start">
          {PLANS.map((p, i) => (
            <Reveal key={p.name} delay={i * 100}>
              <div
                className={`relative h-full rounded-[10px] p-7 border transition-colors ${
                  p.featured
                    ? "border-[#6798ff]/45 bg-[#101216]"
                    : "border-[#1e1e1e] bg-[#101010] hover:border-[#313131]"
                }`}
              >
                {p.featured && (
                  <span className="absolute -top-2.5 left-7 rounded-[4px] bg-[#6798ff] px-2 py-0.5 font-mono text-[10px] tracking-[0.08em] text-[#0a0a0a] uppercase">
                    Most popular
                  </span>
                )}

                <h3 className="text-[15px] font-medium text-white">{p.name}</h3>
                <p className="mt-1 text-[13px] text-[#7c7c7c]">{p.blurb}</p>

                <div className="mt-5 flex items-baseline gap-1.5">
                  <span className="text-[44px] font-medium leading-none tracking-[-0.02em] text-white">
                    {p.price}
                  </span>
                  <span className="text-[14px] text-[#7c7c7c]">{p.cadence}</span>
                </div>

                <Link
                  href="/app"
                  className={`mt-6 flex items-center justify-center rounded-lg px-4 py-2.5 text-[14px] font-medium transition-colors ${
                    p.featured
                      ? "bg-white text-[#0a0a0a] hover:bg-white/90"
                      : "border border-[#313131] text-white hover:border-[#454545] hover:bg-white/[0.03]"
                  }`}
                >
                  {p.cta}
                </Link>

                <ul className="mt-7 space-y-3">
                  {p.features.map((f) => (
                    <li key={f} className="flex items-start gap-2.5 text-[14px] text-[#a7a7a7]">
                      <Check className="w-4 h-4 mt-0.5 shrink-0 text-[#6798ff]" />
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </Reveal>
          ))}
        </div>

        <p className="mt-10 text-center font-mono text-[11px] tracking-[0.06em] text-[#7c7c7c] uppercase">
          Free during beta · No credit card · Cancel anytime
        </p>
      </div>
    </section>
  );
}

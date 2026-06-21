"use client";

import Link from "next/link";
import { ArrowRight, Star } from "lucide-react";
import { CommandCenterPreview } from "./CommandCenterPreview";

export function HeroSection() {
  return (
    <section className="relative px-6 pt-32 lg:pt-40 pb-20">
      <div className="mx-auto max-w-[1200px] grid lg:grid-cols-[minmax(0,1fr)_minmax(0,1.08fr)] gap-12 xl:gap-16 items-center">
        {/* Copy */}
        <div className="max-w-xl">
          {/* Eyebrow */}
          <div
            className="inline-flex items-center gap-2 rounded-full border border-[#1e1e1e] bg-[#0e0e0e] pl-2.5 pr-3 py-1.5 animate-fade-in-up"
            style={{ opacity: 0 }}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-[#6798ff]" />
            <span className="font-mono text-[11px] tracking-[0.1em] text-[#a7a7a7] uppercase">
              Vertical AI for independent F&amp;B
            </span>
          </div>

          {/* Headline */}
          <h1
            className="mt-6 text-[33px] sm:text-[48px] lg:text-[60px] font-medium leading-[1.05] tracking-[-0.03em] text-balance text-white animate-fade-in-up"
            style={{ opacity: 0, animationDelay: "0.08s" }}
          >
            Run your restaurant.
            <br />
            PHOW <span className="dt-shimmer">watches the market.</span>
          </h1>

          {/* Subtext */}
          <p
            className="mt-6 text-[16px] sm:text-[17px] leading-[1.6] text-[#a7a7a7] animate-fade-in-up"
            style={{ opacity: 0, animationDelay: "0.16s" }}
          >
            The AI analyst and 24/7 market watchtower for indie cafés and restaurants.
            Feasibility studies, competitor moves, reputation, and a daily brief over your
            real signals — the intelligence chains pay{" "}
            <span className="text-white">$15,000</span> for, for the price of two coffees.
          </p>

          {/* CTAs */}
          <div
            className="mt-8 flex flex-wrap items-center gap-3 animate-fade-in-up"
            style={{ opacity: 0, animationDelay: "0.24s" }}
          >
            <Link
              href="/app"
              className="group inline-flex items-center gap-2 rounded-lg bg-white px-5 py-3 text-[15px] font-medium text-[#0a0a0a] hover:bg-white/90 transition-colors"
            >
              Start free
              <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-0.5" />
            </Link>
            <a
              href="#how"
              className="inline-flex items-center gap-2 rounded-lg border border-[#313131] px-5 py-3 text-[15px] font-medium text-white hover:border-[#454545] hover:bg-white/[0.03] transition-colors"
            >
              See how it works
            </a>
          </div>

          {/* Microcopy */}
          <p
            className="mt-6 font-mono text-[11px] tracking-[0.06em] text-[#7c7c7c] uppercase animate-fade-in-up"
            style={{ opacity: 0, animationDelay: "0.32s" }}
          >
            No credit card · Free during beta · Built for F&amp;B owners
          </p>

          {/* Mini trust */}
          <div
            className="mt-6 flex items-center gap-3 animate-fade-in-up"
            style={{ opacity: 0, animationDelay: "0.4s" }}
          >
            <div className="flex">
              {[0, 1, 2, 3, 4].map((i) => (
                <Star key={i} className="w-4 h-4 fill-[#6798ff] text-[#6798ff]" />
              ))}
            </div>
            <span className="text-[13px] text-[#a7a7a7]">
              Loved by early independent owners
            </span>
          </div>
        </div>

        {/* Product preview */}
        <div className="animate-fade-in-up" style={{ opacity: 0, animationDelay: "0.3s" }}>
          <CommandCenterPreview />
        </div>
      </div>
    </section>
  );
}

"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Reveal } from "./Reveal";

export function CTASection() {
  return (
    <section className="px-6 py-20 lg:py-28">
      <div className="mx-auto max-w-[1000px]">
        <Reveal>
          <div className="relative overflow-hidden rounded-[14px] border border-[#1e1e1e] bg-[#0c0c0c] px-6 py-16 sm:px-12 sm:py-20 text-center">
            {/* in-card grid + glow */}
            <div className="dt-grid absolute inset-0 opacity-70" aria-hidden />
            <div
              className="absolute inset-0"
              aria-hidden
              style={{
                background:
                  "radial-gradient(50% 60% at 50% 0%, rgba(103,152,255,0.16), transparent 70%)",
              }}
            />
            <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[#6798ff]/40 to-transparent" />

            <div className="relative">
              <h2 className="text-[34px] sm:text-[46px] font-medium leading-[1.08] tracking-[-0.03em] text-white">
                Give your storefront
                <br />
                an <span className="dt-shimmer">analyst.</span>
              </h2>
              <p className="mt-5 max-w-md mx-auto text-[16px] leading-[1.6] text-[#a7a7a7]">
                Set up your location in two minutes. Wake up tomorrow to your first brief on
                what moved in your market overnight.
              </p>

              <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
                <Link
                  href="/app"
                  className="group inline-flex items-center gap-2 rounded-lg bg-white px-6 py-3 text-[15px] font-medium text-[#0a0a0a] hover:bg-white/90 transition-colors"
                >
                  Start free
                  <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-0.5" />
                </Link>
                <a
                  href="#platform"
                  className="inline-flex items-center gap-2 rounded-lg border border-[#313131] px-6 py-3 text-[15px] font-medium text-white hover:border-[#454545] hover:bg-white/[0.03] transition-colors"
                >
                  See the platform
                </a>
              </div>

              <p className="mt-6 font-mono text-[11px] tracking-[0.06em] text-[#7c7c7c] uppercase">
                Free during beta · No credit card required
              </p>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}

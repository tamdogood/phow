"use client";

import { useIntersectionObserver } from "@/hooks/useIntersectionObserver";
import { Wallet, Clock, RefreshCw } from "lucide-react";
import { Reveal } from "./Reveal";

const CONTRASTS = [
  { Icon: Wallet, stat: "50–100×", label: "cheaper than an agency" },
  { Icon: Clock, stat: "minutes", label: "not weeks of waiting" },
  { Icon: RefreshCw, stat: "live", label: "not a stale snapshot" },
];

export function CostCompareSection() {
  const { ref, isVisible } = useIntersectionObserver<HTMLDivElement>({ threshold: 0.35 });

  return (
    <section className="px-6 py-20 lg:py-28">
      <div className="mx-auto max-w-[1000px]">
        <Reveal className="max-w-2xl mx-auto text-center">
          <p className="font-mono text-[12px] tracking-[0.12em] text-[#a7a7a7] uppercase">
            The math
          </p>
          <h2 className="mt-5 text-[32px] sm:text-[40px] font-medium leading-[1.12] tracking-[-0.025em] text-white">
            What this used to cost
          </h2>
          <p className="mt-5 text-[16px] leading-[1.6] text-[#a7a7a7]">
            A single location study from a market-research agency runs five figures and takes
            weeks. PHOW is a subscription — and it never stops watching.
          </p>
        </Reveal>

        {/* Scale bars */}
        <div ref={ref} className="mt-14 dt-card p-7 sm:p-9">
          {/* Agency */}
          <div className="flex items-end justify-between mb-2.5">
            <span className="text-[14px] text-[#a7a7a7]">Traditional agency · per study</span>
            <span className="font-mono text-[11px] tracking-wide text-[#7c7c7c]">2–6 WEEKS</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="relative h-11 flex-1 rounded-lg bg-[#0a0a0a] overflow-hidden border border-[#1e1e1e]">
              <div
                className="h-full rounded-lg bg-gradient-to-r from-[#1e1e1e] to-[#313131] transition-[width] duration-[1400ms] ease-out"
                style={{ width: isVisible ? "100%" : "0%" }}
              />
            </div>
            <span className="w-24 text-right text-[22px] font-medium text-white tabular-nums">
              $15,000
            </span>
          </div>

          {/* PHOW */}
          <div className="flex items-end justify-between mt-7 mb-2.5">
            <span className="text-[14px] text-white">PHOW · per month</span>
            <span className="font-mono text-[11px] tracking-wide text-[#6798ff]">MINUTES</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="relative h-11 flex-1 rounded-lg bg-[#0a0a0a] overflow-hidden border border-[#1e1e1e]">
              <div
                className="h-full rounded-lg bg-gradient-to-r from-[#4f7fe8] to-[#6798ff] transition-[width] duration-[1400ms] ease-out delay-200"
                style={{ width: isVisible ? "2.4%" : "0%", minWidth: isVisible ? "10px" : "0" }}
              />
            </div>
            <span className="w-24 text-right text-[22px] font-medium text-[#6798ff] tabular-nums">
              $79
            </span>
          </div>

          <p className="mt-8 pt-6 border-t border-[#1a1a1a] text-[15px] leading-[1.6] text-[#a7a7a7]">
            One avoided bad lease — or one recovered 1★ review — pays for{" "}
            <span className="text-white">years</span>.
          </p>
        </div>

        {/* Contrast chips */}
        <div className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-5">
          {CONTRASTS.map((c, i) => (
            <Reveal key={c.label} delay={i * 100}>
              <div className="flex items-center gap-3.5 dt-card p-5">
                <span className="grid place-items-center w-10 h-10 rounded-lg bg-[#6798ff]/12 text-[#6798ff] shrink-0">
                  <c.Icon className="w-5 h-5" strokeWidth={1.75} />
                </span>
                <div>
                  <p className="text-[18px] font-medium text-white leading-none">{c.stat}</p>
                  <p className="mt-1 text-[13px] text-[#7c7c7c]">{c.label}</p>
                </div>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

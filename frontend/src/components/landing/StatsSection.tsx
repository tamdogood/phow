"use client";

import { Banknote, Zap, Layers, Radar } from "lucide-react";
import { Reveal } from "./Reveal";
import { CountUp } from "./CountUp";

export function StatsSection() {
  return (
    <section className="px-6 py-16 border-y border-[#141414] bg-[#0c0c0c]">
      <div className="mx-auto max-w-[1200px] grid grid-cols-2 lg:grid-cols-4 gap-y-12 gap-x-6">
        <Reveal className="text-center">
          <Banknote className="w-5 h-5 text-[#6798ff] mx-auto" strokeWidth={1.75} />
          <p className="mt-4 text-[36px] sm:text-[40px] font-medium leading-none tracking-[-0.02em] text-white">
            <CountUp value={15000} prefix="$" />
          </p>
          <p className="mt-3 text-[15px] font-medium text-white">Saved per study</p>
          <p className="mt-1 text-[13px] text-[#7c7c7c]">vs. a traditional agency</p>
        </Reveal>

        <Reveal className="text-center" delay={80}>
          <Zap className="w-5 h-5 text-[#6798ff] mx-auto" strokeWidth={1.75} />
          <p className="mt-4 text-[36px] sm:text-[40px] font-medium leading-none tracking-[-0.02em] text-white">
            <CountUp value={12} suffix="s" />
          </p>
          <p className="mt-3 text-[15px] font-medium text-white">To first insight</p>
          <p className="mt-1 text-[13px] text-[#7c7c7c]">not weeks of waiting</p>
        </Reveal>

        <Reveal className="text-center" delay={160}>
          <Layers className="w-5 h-5 text-[#6798ff] mx-auto" strokeWidth={1.75} />
          <p className="mt-4 text-[36px] sm:text-[40px] font-medium leading-none tracking-[-0.02em] text-white">
            <CountUp value={9} />
          </p>
          <p className="mt-3 text-[15px] font-medium text-white">Research domains</p>
          <p className="mt-1 text-[13px] text-[#7c7c7c]">in every feasibility study</p>
        </Reveal>

        <Reveal className="text-center" delay={240}>
          <Radar className="w-5 h-5 text-[#6798ff] mx-auto" strokeWidth={1.75} />
          <p className="mt-4 text-[36px] sm:text-[40px] font-medium leading-none tracking-[-0.02em] text-white">
            <CountUp value={24} suffix="/7" />
          </p>
          <p className="mt-3 text-[15px] font-medium text-white">Market monitoring</p>
          <p className="mt-1 text-[13px] text-[#7c7c7c]">automated, while you work</p>
        </Reveal>
      </div>
    </section>
  );
}

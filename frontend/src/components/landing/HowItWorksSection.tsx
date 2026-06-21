"use client";

import { MapPin, Radar, Sunrise } from "lucide-react";
import { Reveal } from "./Reveal";

const STEPS = [
  {
    n: "01",
    Icon: MapPin,
    title: "Add your storefront",
    desc: "Drop your address or paste your Google listing. We pull your baseline in seconds.",
  },
  {
    n: "02",
    Icon: Radar,
    title: "We start watching",
    desc: "Radar scans your market daily and builds your competitor, rank and rating baselines.",
  },
  {
    n: "03",
    Icon: Sunrise,
    title: "Read your brief, act",
    desc: "Each morning: what changed, why it matters, and the single move worth making today.",
  },
];

export function HowItWorksSection() {
  return (
    <section id="how" className="px-6 py-20 lg:py-28 border-y border-[#141414] bg-[#0c0c0c] scroll-mt-24">
      <div className="mx-auto max-w-[1200px]">
        <Reveal className="max-w-2xl mx-auto text-center">
          <p className="font-mono text-[12px] tracking-[0.12em] text-[#a7a7a7] uppercase">
            How it works
          </p>
          <h2 className="mt-5 text-[32px] sm:text-[40px] font-medium leading-[1.12] tracking-[-0.025em] text-white">
            From signup to your first decision in minutes
          </h2>
        </Reveal>

        <div className="relative mt-16 grid md:grid-cols-3 gap-10 md:gap-6">
          {/* connector line */}
          <div className="hidden md:block absolute top-6 left-[16.66%] right-[16.66%] h-px bg-gradient-to-r from-[#1e1e1e] via-[#313131] to-[#1e1e1e]" />

          {STEPS.map((s, i) => (
            <Reveal key={s.n} delay={i * 120}>
              <div className="relative">
                <div className="flex items-center gap-3">
                  <span className="relative z-10 grid place-items-center w-12 h-12 rounded-full border border-[#262626] bg-[#0a0a0a]">
                    <s.Icon className="w-5 h-5 text-[#6798ff]" strokeWidth={1.75} />
                  </span>
                  <span className="font-mono text-[12px] tracking-[0.15em] text-[#6798ff]">
                    {s.n}
                  </span>
                </div>
                <h3 className="mt-5 text-[19px] font-medium text-white tracking-tight">
                  {s.title}
                </h3>
                <p className="mt-2 text-[15px] leading-[1.6] text-[#a7a7a7] max-w-xs">
                  {s.desc}
                </p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

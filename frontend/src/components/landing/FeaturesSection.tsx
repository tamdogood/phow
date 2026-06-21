"use client";

import {
  FileSearch,
  Radar,
  Newspaper,
  MessageSquareReply,
  Crosshair,
  TrendingUp,
  LucideIcon,
} from "lucide-react";
import { Reveal } from "./Reveal";

interface Feature {
  Icon: LucideIcon;
  name: string;
  desc: string;
  radar?: boolean;
}

const FEATURES: Feature[] = [
  {
    Icon: FileSearch,
    name: "Feasibility Study",
    desc: "A go / no-go verdict on any location or concept — nine sourced domains, scored and explained, in minutes.",
  },
  {
    Icon: Radar,
    name: "Business Radar",
    desc: "We scan your market daily and surface what moved: a new rival, a closure nearby, local news that hits your category.",
    radar: true,
  },
  {
    Icon: Newspaper,
    name: "Daily Brief",
    desc: "One short morning read over your real signals — local rank, rating drift, competitor moves and cost pressure.",
  },
  {
    Icon: MessageSquareReply,
    name: "Reputation Hub",
    desc: "Watch your Google rating drift the moment it happens, then draft on-brand replies in your own voice.",
  },
  {
    Icon: Crosshair,
    name: "Competitor Tracking",
    desc: "Follow rivals' pricing, hours, menus and review velocity over time — and get pinged when they change.",
  },
  {
    Icon: TrendingUp,
    name: "Local Rank",
    desc: "See exactly where you land for the searches that send diners your way — then climb the ones that matter.",
  },
];

export function FeaturesSection() {
  return (
    <section id="platform" className="px-6 py-20 lg:py-28 scroll-mt-24">
      <div className="mx-auto max-w-[1200px]">
        <Reveal className="max-w-2xl mx-auto text-center">
          <p className="font-mono text-[12px] tracking-[0.12em] text-[#a7a7a7] uppercase">
            Platform
          </p>
          <h2 className="mt-5 text-[32px] sm:text-[40px] font-medium leading-[1.12] tracking-[-0.025em] text-white">
            Everything an analyst would do — on autopilot
          </h2>
          <p className="mt-5 text-[16px] leading-[1.6] text-[#a7a7a7]">
            Six tools, one continuously-updated picture of your market. Each runs on your own
            location&apos;s live data, not generic industry averages.
          </p>
        </Reveal>

        <div className="mt-14 grid md:grid-cols-2 lg:grid-cols-3 gap-5">
          {FEATURES.map((f, i) => (
            <Reveal key={f.name} delay={(i % 3) * 90}>
              <div className="dt-card dt-card-hover group relative h-full overflow-hidden p-6">
                <div className="relative inline-grid place-items-center w-11 h-11 rounded-[10px] bg-[#6798ff]/12">
                  {f.radar && (
                    <span
                      className="dt-radar-sweep absolute inset-0 rounded-[10px]"
                      style={{
                        background:
                          "conic-gradient(from 0deg, transparent 0deg, rgba(103,152,255,0.55) 40deg, transparent 80deg)",
                      }}
                      aria-hidden
                    />
                  )}
                  <f.Icon className="relative w-5 h-5 text-[#6798ff]" strokeWidth={1.75} />
                </div>

                <h3 className="mt-5 text-[17px] font-medium text-white tracking-tight">
                  {f.name}
                </h3>
                <p className="mt-2 text-[14.5px] leading-[1.6] text-[#a7a7a7]">{f.desc}</p>

                {/* hairline that warms on hover */}
                <span className="pointer-events-none absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-[#6798ff]/0 to-transparent transition-all duration-300 group-hover:via-[#6798ff]/40" />
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

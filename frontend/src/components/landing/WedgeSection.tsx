"use client";

import { Inbox, Radar, Check, X } from "lucide-react";
import { Reveal } from "./Reveal";

const OLD = [
  "Help you collect & answer reviews",
  "Inbound only — your inbox, your messages",
  "AI bolted on as a +$99 add-on",
  "$399–$999 / month",
];

const PHOW = [
  "Watch the market around you, 24/7",
  "Outward intelligence — rivals, rank, costs, demand",
  "AI-native: research → decision, every day",
  "$0–79 / month",
];

export function WedgeSection() {
  return (
    <section className="px-6 py-20 lg:py-28">
      <div className="mx-auto max-w-[1200px]">
        <Reveal className="max-w-2xl mx-auto text-center">
          <p className="font-mono text-[12px] tracking-[0.12em] text-[#a7a7a7] uppercase">
            The gap
          </p>
          <h2 className="mt-5 text-[32px] sm:text-[40px] font-medium leading-[1.12] tracking-[-0.025em] text-white">
            They watch your inbox.
            <br />
            Nobody watches your market.
          </h2>
          <p className="mt-5 text-[16px] leading-[1.6] text-[#a7a7a7]">
            Every review tool helps you answer messages that already arrived. None tell you a
            rival just opened down the block, your rating slipped, or food costs are about to
            squeeze your category. That outward, decision-grade intelligence is PHOW.
          </p>
        </Reveal>

        <div className="mt-14 grid md:grid-cols-2 gap-5">
          <Reveal>
            <div className="dt-card p-7 h-full">
              <div className="flex items-center gap-2.5">
                <span className="grid place-items-center w-9 h-9 rounded-lg bg-white/[0.04] text-[#7c7c7c]">
                  <Inbox className="w-4.5 h-4.5" strokeWidth={1.75} />
                </span>
                <span className="font-mono text-[11px] tracking-[0.1em] text-[#7c7c7c] uppercase">
                  Review tools today
                </span>
              </div>
              <ul className="mt-6 space-y-3.5">
                {OLD.map((t) => (
                  <li key={t} className="flex items-start gap-3 text-[15px] text-[#7c7c7c]">
                    <X className="w-4 h-4 mt-0.5 shrink-0 text-[#454545]" />
                    <span>{t}</span>
                  </li>
                ))}
              </ul>
            </div>
          </Reveal>

          <Reveal delay={120}>
            <div className="dt-card dt-card-hover p-7 h-full border-[#2a2f3d]">
              <div className="flex items-center gap-2.5">
                <span className="grid place-items-center w-9 h-9 rounded-lg bg-[#6798ff]/12 text-[#6798ff]">
                  <Radar className="w-4.5 h-4.5" strokeWidth={1.75} />
                </span>
                <span className="font-mono text-[11px] tracking-[0.1em] text-[#6798ff] uppercase">
                  PHOW
                </span>
              </div>
              <ul className="mt-6 space-y-3.5">
                {PHOW.map((t) => (
                  <li key={t} className="flex items-start gap-3 text-[15px] text-white">
                    <Check className="w-4 h-4 mt-0.5 shrink-0 text-[#6798ff]" />
                    <span>{t}</span>
                  </li>
                ))}
              </ul>
            </div>
          </Reveal>
        </div>
      </div>
    </section>
  );
}

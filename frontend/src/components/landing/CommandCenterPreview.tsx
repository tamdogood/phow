"use client";

import { useEffect, useRef, useState } from "react";
import { Radar, Star, TrendingUp, ArrowDownRight, ArrowUpRight } from "lucide-react";

/** 14-day "local visibility" series — last bars trend up. */
const BARS = [38, 44, 41, 52, 47, 58, 55, 63, 60, 71, 68, 80, 86, 94];

const SIGNALS = [
  {
    Icon: Radar,
    title: "Competitor opened 0.4 mi away",
    meta: "Luca's Trattoria · 4.7★ · pasta",
    tag: "NEW",
    trend: null,
  },
  {
    Icon: Star,
    title: "Your rating dipped",
    meta: "4.6 → 4.5 · 3 new reviews",
    tag: null,
    trend: "down" as const,
  },
  {
    Icon: TrendingUp,
    title: "Local rank · “pasta near me”",
    meta: "#4 this week · climbing",
    tag: null,
    trend: "up" as const,
  },
];

const AI_LINE =
  "Reply to Tuesday's 2★ review and push your $19 lunch set — projected +8% covers this week.";

function useTypewriter(text: string, speed = 26, startDelay = 1100) {
  const [out, setOut] = useState("");
  const [done, setDone] = useState(false);

  useEffect(() => {
    const reduce =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let i = 0;
    let interval: ReturnType<typeof setInterval>;
    const startTimer = setTimeout(
      () => {
        if (reduce) {
          setOut(text);
          setDone(true);
          return;
        }
        interval = setInterval(() => {
          i += 1;
          setOut(text.slice(0, i));
          if (i >= text.length) {
            clearInterval(interval);
            setDone(true);
          }
        }, speed);
      },
      reduce ? 0 : startDelay
    );
    return () => {
      clearTimeout(startTimer);
      clearInterval(interval);
    };
  }, [text, speed, startDelay]);

  return { out, done };
}

export function CommandCenterPreview() {
  const { out, done } = useTypewriter(AI_LINE);
  const mounted = useRef(false);
  useEffect(() => {
    mounted.current = true;
  }, []);

  return (
    <div className="relative">
      {/* Glow ring behind the frame */}
      <div
        className="absolute -inset-px rounded-[14px] opacity-60 blur-xl"
        style={{
          background:
            "radial-gradient(60% 60% at 50% 0%, rgba(103,152,255,0.28), transparent 70%)",
        }}
        aria-hidden
      />

      {/* Window frame */}
      <div className="relative rounded-[14px] border border-[#1e1e1e] bg-[#0c0c0c] overflow-hidden">
        {/* Top highlight hairline */}
        <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/15 to-transparent" />

        {/* Title bar */}
        <div className="flex items-center justify-between gap-3 px-4 py-3 border-b border-[#1a1a1a] bg-[#0a0a0a]">
          <div className="flex items-center gap-2.5">
            <span className="grid place-items-center w-5 h-5 rounded-[5px] bg-[#6798ff] text-[11px] font-semibold text-[#0a0a0a]">
              P
            </span>
            <span className="text-[13px] text-white/80 font-medium">Command Center</span>
            <span className="ml-1 inline-flex items-center gap-1.5">
              <span className="relative grid place-items-center w-2 h-2">
                <span className="dt-ping absolute inset-0 rounded-full bg-[#6798ff]" />
                <span className="relative w-1.5 h-1.5 rounded-full bg-[#6798ff]" />
              </span>
              <span className="font-mono text-[10px] tracking-[0.12em] text-[#a7a7a7]">LIVE</span>
            </span>
          </div>
          <div className="hidden sm:flex items-center gap-1">
            {["Daily Brief", "Radar", "Feasibility"].map((t, i) => (
              <span
                key={t}
                className={`px-2.5 py-1 rounded-[6px] font-mono text-[10px] tracking-wide ${
                  i === 0 ? "bg-[#181818] text-white border border-[#262626]" : "text-[#7c7c7c]"
                }`}
              >
                {t}
              </span>
            ))}
          </div>
        </div>

        {/* Body */}
        <div className="grid md:grid-cols-2 gap-4 p-4">
          {/* Left — signals / today's brief */}
          <div className="flex flex-col gap-3">
            <p className="font-mono text-[10px] tracking-[0.12em] text-[#7c7c7c] uppercase">
              Today&apos;s Brief · Mon Jun 22
            </p>
            {SIGNALS.map((s, i) => (
              <div
                key={s.title}
                className="dt-card flex items-start gap-3 p-3 dt-reveal dt-in"
                style={{ transitionDelay: `${250 + i * 160}ms` }}
              >
                <span className="grid place-items-center w-8 h-8 rounded-[7px] bg-[#6798ff]/12 text-[#6798ff] shrink-0">
                  <s.Icon className="w-4 h-4" strokeWidth={1.75} />
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <p className="text-[13px] text-white leading-snug truncate">{s.title}</p>
                    {s.tag && (
                      <span className="shrink-0 rounded-[4px] bg-[#6798ff]/15 px-1.5 py-0.5 font-mono text-[9px] tracking-wide text-[#6798ff]">
                        {s.tag}
                      </span>
                    )}
                    {s.trend === "down" && (
                      <ArrowDownRight className="w-3.5 h-3.5 text-[#a7a7a7] shrink-0" />
                    )}
                    {s.trend === "up" && (
                      <ArrowUpRight className="w-3.5 h-3.5 text-[#6798ff] shrink-0" />
                    )}
                  </div>
                  <p className="text-[11.5px] text-[#7c7c7c] mt-0.5 truncate">{s.meta}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Right — chart + AI insight */}
          <div className="flex flex-col gap-4">
            <div className="dt-card p-4">
              <div className="flex items-center justify-between mb-3">
                <p className="text-[12px] text-white/80 font-medium">Local visibility</p>
                <span className="font-mono text-[10px] tracking-wide text-[#7c7c7c]">14 DAYS</span>
              </div>
              <div className="relative h-28">
                {/* baseline grid */}
                <div className="absolute inset-0 flex flex-col justify-between">
                  {[0, 1, 2, 3].map((g) => (
                    <div key={g} className="border-t border-[#171717]" />
                  ))}
                </div>
                <div className="relative h-full flex items-end gap-[3px]">
                  {BARS.map((h, i) => (
                    <div
                      key={i}
                      className="dt-bar flex-1 rounded-t-[2px]"
                      style={{
                        height: `${h}%`,
                        animationDelay: `${400 + i * 55}ms`,
                        background:
                          i >= BARS.length - 2
                            ? "linear-gradient(180deg, #6798ff, #4f7fe8)"
                            : "rgba(103,152,255,0.34)",
                      }}
                    />
                  ))}
                </div>
              </div>
              <div className="mt-3 flex items-center gap-1.5 text-[11px]">
                <ArrowUpRight className="w-3.5 h-3.5 text-[#6798ff]" />
                <span className="text-white">+34%</span>
                <span className="text-[#7c7c7c]">vs. last cycle</span>
              </div>
            </div>

            {/* AI insight (streaming) */}
            <div className="dt-card p-4">
              <p className="font-mono text-[10px] tracking-[0.12em] text-[#6798ff] uppercase mb-2">
                ✦ PHOW recommends
              </p>
              <p className="text-[12.5px] leading-relaxed text-white/90 min-h-[3.6em]">
                {out}
                {!done && <span className="dt-caret align-middle ml-0.5" />}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Floating accent chips */}
      <div className="hidden lg:block">
        <div className="dt-float absolute -top-5 -right-6 rounded-lg border border-[#262626] bg-[#0e0e0e]/95 px-3.5 py-2.5 backdrop-blur">
          <p className="text-[18px] font-medium text-white leading-none">
            $14,200<span className="text-[#6798ff]">+</span>
          </p>
          <p className="font-mono text-[9px] tracking-wide text-[#7c7c7c] mt-1 uppercase">
            saved vs. agency
          </p>
        </div>
        <div className="dt-float-slow absolute top-1/3 -left-7 rounded-lg border border-[#262626] bg-[#0e0e0e]/95 px-3.5 py-2.5 backdrop-blur">
          <p className="text-[18px] font-medium text-white leading-none">12s</p>
          <p className="font-mono text-[9px] tracking-wide text-[#7c7c7c] mt-1 uppercase">
            to insight
          </p>
        </div>
        <div className="dt-float absolute -bottom-5 right-10 rounded-lg border border-[#262626] bg-[#0e0e0e]/95 px-3.5 py-2.5 backdrop-blur" style={{ animationDelay: "1.5s" }}>
          <p className="text-[18px] font-medium text-white leading-none">9</p>
          <p className="font-mono text-[9px] tracking-wide text-[#7c7c7c] mt-1 uppercase">
            research domains
          </p>
        </div>
      </div>
    </div>
  );
}

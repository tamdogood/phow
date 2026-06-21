"use client";

import { MapPin, Star, Building2, LineChart, Newspaper, Navigation } from "lucide-react";

const SOURCES = [
  { Icon: MapPin, label: "Google Maps" },
  { Icon: Star, label: "Google Reviews" },
  { Icon: Building2, label: "U.S. Census" },
  { Icon: LineChart, label: "FRED · Fed Data" },
  { Icon: Newspaper, label: "Local News" },
  { Icon: Navigation, label: "Places API" },
];

export function LogoStrip() {
  return (
    <section className="px-6 py-12 border-y border-[#141414]">
      <div className="mx-auto max-w-[1200px]">
        <p className="text-center font-mono text-[11px] tracking-[0.12em] text-[#7c7c7c] uppercase">
          Built on the data the big players pay for
        </p>

        <div className="dt-marquee-mask mt-7 overflow-hidden">
          <div className="dt-marquee flex w-max items-center gap-12">
            {[...SOURCES, ...SOURCES].map((s, i) => (
              <div key={i} className="flex items-center gap-2.5 text-[#7c7c7c] shrink-0">
                <s.Icon className="w-4 h-4" strokeWidth={1.75} />
                <span className="text-[15px] font-medium tracking-tight whitespace-nowrap">
                  {s.label}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

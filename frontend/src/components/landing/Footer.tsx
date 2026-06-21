"use client";

import Link from "next/link";
import { ArrowUpRight } from "lucide-react";

const COLUMNS: { title: string; links: { label: string; href: string }[] }[] = [
  {
    title: "Platform",
    links: [
      { label: "Feasibility Study", href: "/app" },
      { label: "Business Radar", href: "/radar" },
      { label: "Daily Brief", href: "/dashboard" },
      { label: "Reputation Hub", href: "/reviews" },
      { label: "Competitor Tracking", href: "/app" },
      { label: "Local Rank", href: "/app" },
    ],
  },
  {
    title: "Company",
    links: [
      { label: "Features", href: "/features" },
      { label: "Pricing", href: "#pricing" },
      { label: "About", href: "/about" },
      { label: "Community", href: "/community" },
    ],
  },
  {
    title: "Get started",
    links: [
      { label: "Start free", href: "/app" },
      { label: "Sign in", href: "/auth/signin" },
      { label: "Privacy", href: "#" },
      { label: "Terms", href: "#" },
    ],
  },
];

export function Footer() {
  return (
    <footer className="border-t border-[#141414] px-6 pt-16 pb-10">
      <div className="mx-auto max-w-[1200px]">
        <div className="grid gap-10 md:grid-cols-[1.4fr_1fr_1fr_1fr]">
          {/* Brand */}
          <div>
            <div className="flex items-center gap-2.5">
              <span className="grid place-items-center w-7 h-7 rounded-[7px] bg-[#6798ff] text-[13px] font-bold text-[#0a0a0a]">
                P
              </span>
              <span className="text-[17px] font-semibold tracking-tight text-white">PHOW</span>
            </div>
            <p className="mt-4 max-w-[240px] text-[14px] leading-[1.6] text-[#7c7c7c]">
              The AI analyst and market watchtower for independent restaurants and cafés.
            </p>
            <Link
              href="/app"
              className="group mt-5 inline-flex items-center gap-1.5 text-[14px] text-white"
            >
              Start free
              <ArrowUpRight className="w-3.5 h-3.5 text-[#6798ff] transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
            </Link>
          </div>

          {/* Link columns */}
          {COLUMNS.map((col) => (
            <div key={col.title}>
              <p className="font-mono text-[11px] tracking-[0.12em] text-white uppercase">
                {col.title}
              </p>
              <ul className="mt-4 space-y-3">
                {col.links.map((l) => (
                  <li key={l.label}>
                    <Link
                      href={l.href}
                      className="text-[14px] text-[#a7a7a7] hover:text-white transition-colors"
                    >
                      {l.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div className="mt-14 pt-7 border-t border-[#141414] flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-[13px] text-[#7c7c7c]">
            © {new Date().getFullYear()} PHOW. All rights reserved.
          </p>
          <p className="font-mono text-[11px] tracking-[0.1em] text-[#454545] uppercase">
            Built for independent F&amp;B
          </p>
          <div className="flex items-center gap-3">
            <a
              href="#"
              aria-label="X"
              className="grid place-items-center w-8 h-8 rounded-lg text-[#7c7c7c] hover:text-white hover:bg-white/[0.04] transition-colors"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
              </svg>
            </a>
            <a
              href="#"
              aria-label="GitHub"
              className="grid place-items-center w-8 h-8 rounded-lg text-[#7c7c7c] hover:text-white hover:bg-white/[0.04] transition-colors"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
              </svg>
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}

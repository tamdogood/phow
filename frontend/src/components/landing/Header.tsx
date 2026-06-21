"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, Menu, X } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

const NAV_LINKS = [
  { label: "Platform", href: "#platform" },
  { label: "How it works", href: "#how" },
  { label: "Pricing", href: "#pricing" },
];

export function Header() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const { user, loading } = useAuth();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header className="fixed top-0 inset-x-0 z-50">
      {/* Promo strip */}
      <div className="hidden sm:flex items-center justify-center gap-2 h-9 border-b border-[#141414] bg-[#0a0a0a] text-[12px]">
        <span className="text-[#6798ff]">◆</span>
        <span className="text-white/70">Now in beta —</span>
        <span className="text-white">every tool free.</span>
        <Link href="/app" className="group inline-flex items-center gap-1 text-[#a7a7a7] hover:text-white transition-colors">
          Claim your storefront
          <ArrowRight className="w-3 h-3 transition-transform group-hover:translate-x-0.5" />
        </Link>
      </div>

      {/* Nav */}
      <div
        className={`border-b transition-colors ${
          scrolled
            ? "border-[#1a1a1a] bg-[#0a0a0a]/85 backdrop-blur-md"
            : "border-transparent bg-transparent"
        }`}
      >
        <div className="mx-auto max-w-[1200px] px-6 h-16 flex items-center justify-between">
          {/* Brand */}
          <div className="flex items-center gap-3">
            <Link href="/" className="flex items-center gap-2.5">
              <span className="grid place-items-center w-7 h-7 rounded-[7px] bg-[#6798ff] text-[13px] font-bold text-[#0a0a0a]">
                P
              </span>
              <span className="text-[17px] font-semibold tracking-tight text-white">PHOW</span>
            </Link>
            <span className="hidden md:inline-flex font-mono text-[10px] tracking-[0.1em] text-[#7c7c7c] uppercase border-l border-[#262626] pl-3">
              F&amp;B Intelligence
            </span>
          </div>

          {/* Center nav */}
          <nav className="hidden md:flex items-center gap-1">
            {NAV_LINKS.map((l) => (
              <a
                key={l.href}
                href={l.href}
                className="px-3.5 py-2 rounded-full text-[14px] text-[#a7a7a7] hover:text-white hover:bg-white/[0.04] transition-colors"
              >
                {l.label}
              </a>
            ))}
          </nav>

          {/* Right CTAs */}
          <div className="hidden md:flex items-center gap-2">
            {!loading &&
              (user ? (
                <Link
                  href="/app"
                  className="inline-flex items-center gap-1.5 rounded-lg bg-white px-3.5 py-2 text-[14px] font-medium text-[#0a0a0a] hover:bg-white/90 transition-colors"
                >
                  Go to app
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              ) : (
                <>
                  <Link
                    href="/auth/signin"
                    className="px-3.5 py-2 text-[14px] text-[#a7a7a7] hover:text-white transition-colors"
                  >
                    Sign in
                  </Link>
                  <Link
                    href="/app"
                    className="inline-flex items-center gap-1.5 rounded-lg bg-white px-3.5 py-2 text-[14px] font-medium text-[#0a0a0a] hover:bg-white/90 transition-colors"
                  >
                    Start free
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </>
              ))}
          </div>

          {/* Mobile toggle */}
          <button
            onClick={() => setMobileOpen((v) => !v)}
            className="md:hidden grid place-items-center w-9 h-9 rounded-lg text-white hover:bg-white/5 transition-colors"
            aria-label="Toggle menu"
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>

        {/* Mobile panel */}
        {mobileOpen && (
          <div className="md:hidden border-t border-[#1a1a1a] bg-[#0a0a0a] px-6 py-4">
            <nav className="flex flex-col gap-1">
              {NAV_LINKS.map((l) => (
                <a
                  key={l.href}
                  href={l.href}
                  onClick={() => setMobileOpen(false)}
                  className="px-2 py-2.5 rounded-lg text-[15px] text-[#a7a7a7] hover:text-white hover:bg-white/[0.04] transition-colors"
                >
                  {l.label}
                </a>
              ))}
              <div className="mt-3 flex flex-col gap-2">
                {!user && (
                  <Link
                    href="/auth/signin"
                    onClick={() => setMobileOpen(false)}
                    className="rounded-lg border border-[#262626] px-4 py-2.5 text-center text-[14px] text-white"
                  >
                    Sign in
                  </Link>
                )}
                <Link
                  href="/app"
                  onClick={() => setMobileOpen(false)}
                  className="rounded-lg bg-white px-4 py-2.5 text-center text-[14px] font-medium text-[#0a0a0a]"
                >
                  {user ? "Go to app" : "Start free"}
                </Link>
              </div>
            </nav>
          </div>
        )}
      </div>
    </header>
  );
}

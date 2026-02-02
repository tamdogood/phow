"use client";

import { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";

export function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { user, loading: authLoading } = useAuth();

  return (
    <header className="fixed top-0 left-0 right-0 z-50 px-6 py-4 bg-[#0a0a0a]/80 backdrop-blur-md border-b border-white/5">
      <div className="mx-auto max-w-6xl flex items-center justify-between">
        {/* Logo + Badge */}
        <div className="flex items-center gap-3">
          <Link href="/" className="text-xl font-bold text-white hover:text-white/80 transition-colors tracking-tight">
            PHOW
          </Link>
          <span className="hidden sm:inline-flex items-center px-2 py-0.5 rounded bg-white/10 text-[10px] font-mono text-white/60 uppercase tracking-wider">
            AI Analytics
          </span>
        </div>

        {/* Desktop CTAs */}
        <div className="hidden md:flex items-center gap-3">
          {!authLoading && (
            <>
              {user ? (
                <Link
                  href="/app"
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white text-black text-sm font-medium hover:bg-white/90 transition-all"
                >
                  Go to App
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </Link>
              ) : (
                <>
                  <Link
                    href="/auth/signin"
                    className="px-4 py-2 text-white/70 hover:text-white text-sm font-medium transition-colors"
                  >
                    Sign In
                  </Link>
                  <Link
                    href="/app"
                    className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white text-black text-sm font-medium hover:bg-white/90 transition-all"
                  >
                    Get Started
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </Link>
                </>
              )}
            </>
          )}
        </div>

        {/* Mobile Menu Button */}
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="md:hidden p-2 text-white hover:bg-white/10 rounded-lg transition-colors"
          aria-label="Toggle menu"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            {mobileMenuOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden mt-4 pb-4 border-t border-white/10">
          <nav className="flex flex-col gap-2 mt-4">
            {!authLoading && (
              <>
                {user ? (
                  <Link
                    href="/app"
                    className="px-4 py-2 rounded-lg bg-white text-black text-sm font-medium text-center"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    Go to App
                  </Link>
                ) : (
                  <>
                    <Link
                      href="/auth/signin"
                      className="px-4 py-2 text-white/70 hover:text-white text-sm font-medium text-left"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      Sign In
                    </Link>
                    <Link
                      href="/app"
                      className="px-4 py-2 rounded-lg bg-white text-black text-sm font-medium text-center"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      Get Started
                    </Link>
                  </>
                )}
              </>
            )}
          </nav>
        </div>
      )}
    </header>
  );
}

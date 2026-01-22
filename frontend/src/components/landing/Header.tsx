"use client";

import { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";

export function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { user, loading: authLoading, isConfigured, signInWithGoogle } = useAuth();

  return (
    <header className="glass-header fixed top-0 left-0 right-0 z-50 px-6 py-4">
      <div className="mx-auto max-w-6xl flex items-center justify-between">
        {/* Logo + Navigation */}
        <div className="flex items-center gap-8">
          <Link href="/" className="text-2xl font-bold text-white hover:text-white/80 transition-colors">
            PHOW
          </Link>
          <nav className="hidden md:flex items-center gap-6">
            <Link href="/features" className="text-white/70 hover:text-white transition-colors text-sm font-medium">
              Features
            </Link>
            <Link href="/about" className="text-white/70 hover:text-white transition-colors text-sm font-medium">
              About
            </Link>
          </nav>
        </div>

        {/* Desktop CTAs */}
        <div className="hidden md:flex items-center gap-3">
          {!authLoading && (
            <>
              {user ? (
                <>
                  <Link
                    href="/dashboard"
                    className="px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white text-sm font-medium transition-all border border-white/20"
                  >
                    Dashboard
                  </Link>
                  <Link
                    href="/app"
                    className="px-4 py-2 rounded-lg bg-gradient-to-r from-sky-500 to-blue-600 text-white text-sm font-medium hover:from-sky-400 hover:to-blue-500 transition-all shadow-lg shadow-sky-500/25"
                  >
                    Go to App
                  </Link>
                </>
              ) : (
                <>
                  <button
                    onClick={signInWithGoogle}
                    disabled={!isConfigured}
                    className="px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white text-sm font-medium transition-all border border-white/20 disabled:opacity-50"
                  >
                    Sign In
                  </button>
                  <Link
                    href="/app"
                    className="px-4 py-2 rounded-lg bg-gradient-to-r from-sky-500 to-blue-600 text-white text-sm font-medium hover:from-sky-400 hover:to-blue-500 transition-all shadow-lg shadow-sky-500/25"
                  >
                    Get Started
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
            <Link
              href="/features"
              className="px-4 py-2 text-white/70 hover:text-white hover:bg-white/10 rounded-lg transition-all text-sm font-medium"
              onClick={() => setMobileMenuOpen(false)}
            >
              Features
            </Link>
            <Link
              href="/about"
              className="px-4 py-2 text-white/70 hover:text-white hover:bg-white/10 rounded-lg transition-all text-sm font-medium"
              onClick={() => setMobileMenuOpen(false)}
            >
              About
            </Link>
            <hr className="border-white/10 my-2" />
            {!authLoading && (
              <>
                {user ? (
                  <>
                    <Link
                      href="/dashboard"
                      className="px-4 py-2 text-white/70 hover:text-white hover:bg-white/10 rounded-lg transition-all text-sm font-medium"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      Dashboard
                    </Link>
                    <Link
                      href="/app"
                      className="px-4 py-2 rounded-lg bg-gradient-to-r from-sky-500 to-blue-600 text-white text-sm font-medium text-center"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      Go to App
                    </Link>
                  </>
                ) : (
                  <>
                    <button
                      onClick={() => {
                        signInWithGoogle();
                        setMobileMenuOpen(false);
                      }}
                      disabled={!isConfigured}
                      className="px-4 py-2 text-white/70 hover:text-white hover:bg-white/10 rounded-lg transition-all text-sm font-medium text-left disabled:opacity-50"
                    >
                      Sign In
                    </button>
                    <Link
                      href="/app"
                      className="px-4 py-2 rounded-lg bg-gradient-to-r from-sky-500 to-blue-600 text-white text-sm font-medium text-center"
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

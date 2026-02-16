"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";

function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  const pathname = usePathname();
  const isActive = pathname === href || pathname.startsWith(href + "/");

  return (
    <Link
      href={href}
      className={`px-4 py-2 text-sm font-medium transition-colors ${
        isActive ? "text-white" : "text-white/70 hover:text-white"
      }`}
    >
      {children}
    </Link>
  );
}

export function AppHeader({ maxWidth = "max-w-6xl" }: { maxWidth?: string }) {
  const { user, loading: authLoading } = useAuth();

  return (
    <header className="dark-header fixed top-0 left-0 right-0 z-50 px-6 py-4">
      <div className={`mx-auto ${maxWidth} flex items-center justify-between`}>
        <div className="flex items-center gap-3">
          <Link href="/" className="text-xl font-bold text-white hover:text-white/80 transition-colors tracking-tight">
            PHOW
          </Link>
          <span className="hidden sm:inline-flex items-center px-2 py-0.5 rounded bg-white/10 text-[10px] font-mono text-white/60 uppercase tracking-wider">
            AI Analytics
          </span>
        </div>

        <div className="hidden md:flex items-center gap-1">
          {!authLoading && (
            <>
              {user ? (
                <>
                  <NavLink href="/dashboard">Dashboard</NavLink>
                  <NavLink href="/app">Chat</NavLink>
                  <Link
                    href="/profile"
                    className="ml-2 flex items-center gap-2 px-4 py-2 rounded-lg bg-white text-black text-sm font-medium hover:bg-white/90 transition-all"
                  >
                    {user.user_metadata?.full_name || user.email?.split("@")[0] || "Profile"}
                  </Link>
                </>
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
                  </Link>
                </>
              )}
            </>
          )}
        </div>
      </div>
    </header>
  );
}

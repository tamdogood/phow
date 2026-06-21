"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Radar } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  const pathname = usePathname();
  const isActive = pathname === href || pathname.startsWith(href + "/");

  return (
    <Link
      href={href}
      className={cn(
        "relative rounded-lg px-3 py-1.5 text-sm font-medium transition-colors",
        isActive ? "text-white bg-white/[0.06]" : "text-white/60 hover:text-white hover:bg-white/[0.04]"
      )}
    >
      {children}
    </Link>
  );
}

function BrandMark() {
  return (
    <Link href="/" className="group flex items-center gap-2.5">
      <span className="relative grid h-8 w-8 place-items-center rounded-[0.6rem] bg-gradient-to-br from-blue-500 to-indigo-600 shadow-[0_4px_14px_rgba(59,130,246,0.45)] ring-1 ring-white/15">
        <Radar className="h-4 w-4 text-white" strokeWidth={2.4} />
      </span>
      <span className="flex flex-col leading-none">
        <span className="text-[15px] font-semibold tracking-tight text-white transition-colors group-hover:text-white/90">
          PHOW
        </span>
        <span className="text-[9px] font-medium uppercase tracking-[0.18em] text-white/40">
          AI Analytics
        </span>
      </span>
    </Link>
  );
}

function Avatar({ name }: { name: string }) {
  const initial = name.trim().charAt(0).toUpperCase() || "U";
  return (
    <span className="grid h-6 w-6 place-items-center rounded-full bg-gradient-to-br from-blue-500/90 to-indigo-600/90 text-[11px] font-semibold text-white ring-1 ring-white/15">
      {initial}
    </span>
  );
}

export function AppHeader({ maxWidth = "max-w-6xl" }: { maxWidth?: string }) {
  const { user, loading: authLoading } = useAuth();
  const displayName = user?.user_metadata?.full_name || user?.email?.split("@")[0] || "Profile";

  return (
    <header className="dark-header fixed top-0 left-0 right-0 z-50 px-6 py-4">
      <div className={cn("mx-auto flex items-center justify-between gap-4", maxWidth)}>
        <BrandMark />

        {!authLoading && (
          <div className="flex items-center gap-2">
            {user ? (
              <>
                <nav className="hidden md:flex items-center gap-1">
                  <NavLink href="/dashboard">Dashboard</NavLink>
                  <NavLink href="/radar">Radar</NavLink>
                  <NavLink href="/reviews">Reputation</NavLink>
                  <NavLink href="/app">Chat</NavLink>
                </nav>
                <Link
                  href="/profile"
                  className="ml-1 flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] py-1 pl-1 pr-3 text-sm font-medium text-white/80 transition-colors hover:border-white/20 hover:text-white"
                >
                  <Avatar name={displayName} />
                  <span className="hidden sm:inline max-w-[120px] truncate">{displayName}</span>
                </Link>
              </>
            ) : (
              <>
                <Link
                  href="/auth/signin"
                  className="hidden sm:inline-flex rounded-lg px-3 py-1.5 text-sm font-medium text-white/60 transition-colors hover:text-white hover:bg-white/[0.04]"
                >
                  Sign In
                </Link>
                <Button asChild size="sm">
                  <Link href="/app">Get Started</Link>
                </Button>
              </>
            )}
          </div>
        )}
      </div>
    </header>
  );
}

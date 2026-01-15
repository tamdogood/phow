"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";

export default function SignInPage() {
  const router = useRouter();
  const { user, loading, signInWithGoogle } = useAuth();

  // Redirect if already signed in
  useEffect(() => {
    if (!loading && user) {
      router.push("/");
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900">
        <div className="text-white">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Background */}
      <div
        className="absolute inset-0 z-0"
        style={{
          backgroundImage: `url('https://plus.unsplash.com/premium_photo-1664443577580-dd2674e9d359?q=80&w=2071&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D')`,
          backgroundSize: "cover",
          backgroundPosition: "center",
        }}
      />
      <div className="absolute inset-0 z-0 bg-gradient-to-b from-slate-900/40 via-transparent to-slate-900/60" />

      {/* Header */}
      <header className="glass-header fixed top-0 left-0 right-0 z-50 px-6 py-4">
        <div className="mx-auto max-w-6xl flex items-center justify-between">
          <Link
            href="/"
            className="text-xl font-bold text-white hover:text-white/80 transition-colors"
          >
            <span className="text-2xl">PHOW</span>
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative z-10 pt-24 pb-12 px-6">
        <div className="max-w-md mx-auto">
          <div className="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 p-8 text-center">
            <h1 className="text-2xl font-bold text-white mb-2">Welcome to PHOW</h1>
            <p className="text-white/70 mb-8">
              Sign in to save your business profile and get personalized insights.
            </p>

            <button
              onClick={signInWithGoogle}
              className="w-full px-6 py-3 rounded-lg bg-white text-slate-900 font-medium hover:bg-white/90 transition-all flex items-center justify-center gap-3"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path
                  fill="currentColor"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="currentColor"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="currentColor"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                />
                <path
                  fill="currentColor"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
              Continue with Google
            </button>

            <p className="text-white/50 text-sm mt-6">
              By signing in, you agree to our Terms of Service.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}

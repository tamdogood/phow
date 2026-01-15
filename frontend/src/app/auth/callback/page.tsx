"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { getBusinessProfile } from "@/lib/api";

export default function AuthCallbackPage() {
  const router = useRouter();
  const { user, loading } = useAuth();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    async function handleCallback() {
      if (loading) return;

      if (!user) {
        // No user after callback - redirect to signin
        router.push("/auth/signin");
        return;
      }

      // Check if user has a business profile
      try {
        const profile = await getBusinessProfile(user.id, "user");
        if (profile) {
          // Existing user with profile - go home
          router.push("/");
        } else {
          // New user - redirect to business setup
          router.push("/business-setup");
        }
      } catch {
        // No profile found - redirect to business setup
        router.push("/business-setup");
      }

      setChecking(false);
    }

    handleCallback();
  }, [user, loading, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-4"></div>
        <p className="text-white/70">
          {checking ? "Completing sign in..." : "Redirecting..."}
        </p>
      </div>
    </div>
  );
}

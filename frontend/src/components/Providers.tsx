"use client";

import { ReactNode } from "react";
import { AuthProvider } from "@/contexts/AuthContext";
import "@/lib/api-mock"; // installs /api/* fetch mock when NEXT_PUBLIC_API_MOCK=1 (no-op otherwise)

export function Providers({ children }: { children: ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>;
}

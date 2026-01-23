"use client";

import {
  Header,
  Footer,
  HeroSection,
  DemoSection,
  FeaturesSection,
  CTASection,
} from "@/components/landing";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] relative">
      {/* Grid pattern overlay */}
      <div className="fixed inset-0 grid-pattern pointer-events-none" />

      <Header />
      <main className="relative z-10">
        <HeroSection />
        <DemoSection />
        <FeaturesSection />
        <CTASection />
      </main>
      <Footer />
    </div>
  );
}

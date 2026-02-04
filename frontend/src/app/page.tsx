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
    <div className="min-h-screen bg-white relative">
      {/* Grid pattern overlay */}
      <div className="fixed inset-0 grid-pattern-light pointer-events-none" />

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

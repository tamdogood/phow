"use client";

import {
  Header,
  Footer,
  HeroSection,
  LogoStrip,
  WedgeSection,
  StatsSection,
  FeaturesSection,
  HowItWorksSection,
  CostCompareSection,
  TestimonialsSection,
  PricingSection,
  CTASection,
} from "@/components/landing";

export default function LandingPage() {
  return (
    <div className="relative min-h-screen bg-[#0a0a0a] text-white overflow-x-hidden">
      {/* Blueprint grid + indigo command-center glow */}
      <div className="pointer-events-none fixed inset-0 dt-grid" aria-hidden />
      <div className="pointer-events-none absolute inset-x-0 top-0 h-[90vh] dt-glow" aria-hidden />

      <Header />
      <main className="relative z-10">
        <HeroSection />
        <LogoStrip />
        <WedgeSection />
        <StatsSection />
        <FeaturesSection />
        <HowItWorksSection />
        <CostCompareSection />
        <TestimonialsSection />
        <PricingSection />
        <CTASection />
      </main>
      <Footer />
    </div>
  );
}

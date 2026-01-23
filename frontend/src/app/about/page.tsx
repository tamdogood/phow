"use client";

import Link from "next/link";
import { Header, Footer } from "@/components/landing";
import { useIntersectionObserver } from "@/hooks/useIntersectionObserver";

const values = [
  {
    icon: "🎯",
    title: "Data-Driven Decisions",
    description: "We believe every business owner deserves access to the same quality insights that big corporations have.",
  },
  {
    icon: "💡",
    title: "Simplicity First",
    description: "Complex analysis, simple answers. We turn complicated data into actionable recommendations.",
  },
  {
    icon: "🤝",
    title: "Small Business Focus",
    description: "Built specifically for small business owners, not enterprise. Your needs come first.",
  },
  {
    icon: "🔒",
    title: "Privacy Matters",
    description: "Your business data stays private. We never share or sell your information.",
  },
];

const stats = [
  { value: "1,000+", label: "Business Owners" },
  { value: "10,000+", label: "Analyses Run" },
  { value: "50+", label: "Cities Covered" },
  { value: "4.9/5", label: "User Rating" },
];

function ValuesSection() {
  const { ref, isVisible } = useIntersectionObserver<HTMLElement>({ threshold: 0.1 });

  return (
    <section ref={ref} className="py-24 px-6 border-t border-white/5">
      <div className="mx-auto max-w-6xl">
        <div className={`text-center mb-16 animate-on-scroll ${isVisible ? "visible" : ""}`}>
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Our Values</h2>
          <p className="text-lg text-white/50 max-w-2xl mx-auto">
            The principles that guide everything we build.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {values.map((value, index) => (
            <div
              key={value.title}
              className={`dark-card p-8 hover-lift animate-on-scroll ${isVisible ? "visible" : ""}`}
              style={{ transitionDelay: `${(index + 1) * 100}ms` }}
            >
              <div className="text-4xl mb-4">{value.icon}</div>
              <h3 className="text-xl font-semibold text-white mb-2">{value.title}</h3>
              <p className="text-white/50">{value.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function StatsSection() {
  const { ref, isVisible } = useIntersectionObserver<HTMLElement>({ threshold: 0.1 });

  return (
    <section ref={ref} className="py-24 px-6 bg-[#111]">
      <div className="mx-auto max-w-6xl">
        <div className={`grid grid-cols-2 md:grid-cols-4 gap-8 animate-on-scroll ${isVisible ? "visible" : ""}`}>
          {stats.map((stat, index) => (
            <div
              key={stat.label}
              className="text-center"
              style={{ transitionDelay: `${(index + 1) * 100}ms` }}
            >
              <p className="text-4xl md:text-5xl font-bold text-white mb-2">{stat.value}</p>
              <p className="text-white/50">{stat.label}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export default function AboutPage() {
  const { ref: heroRef, isVisible: heroVisible } = useIntersectionObserver<HTMLElement>({ threshold: 0.1 });

  return (
    <div className="min-h-screen bg-[#0a0a0a] relative overflow-hidden">
      {/* Grid pattern overlay */}
      <div className="fixed inset-0 grid-pattern pointer-events-none" />

      <Header />

      <main className="relative z-10 pt-32">
        {/* Hero */}
        <section ref={heroRef} className="px-6 pb-24">
          <div className="mx-auto max-w-4xl text-center">
            <h1 className={`text-4xl md:text-5xl font-bold text-white mb-6 tracking-tight animate-on-scroll ${heroVisible ? "visible" : ""}`}>
              About <span className="text-accent-blue">PHOW</span>
            </h1>
            <p className={`text-xl text-white/60 mb-8 animate-on-scroll ${heroVisible ? "visible" : ""}`} style={{ transitionDelay: "100ms" }}>
              We&apos;re on a mission to level the playing field for small business owners.
            </p>
          </div>
        </section>

        {/* Story */}
        <section className="py-24 px-6 bg-[#111]">
          <div className="mx-auto max-w-4xl">
            <div className="dark-card p-8 md:p-12 animate-fade-in-up">
              <h2 className="text-2xl md:text-3xl font-bold text-white mb-6">Our Story</h2>
              <div className="space-y-4 text-white/60 text-lg">
                <p>
                  PHOW started with a simple observation: big businesses have armies of analysts and expensive tools to make data-driven decisions. Small business owners? They rely on gut feelings and hope for the best.
                </p>
                <p>
                  We believed that wasn&apos;t fair. Every entrepreneur deserves access to powerful analytics—regardless of their budget or technical expertise.
                </p>
                <p>
                  So we built PHOW: an AI-powered platform that puts enterprise-grade business intelligence in the hands of small business owners. No PhD in data science required. Just ask questions in plain English and get actionable insights.
                </p>
                <p>
                  Whether you&apos;re opening your first coffee shop, validating a new product idea, or trying to understand your competition—PHOW is here to help you make smarter decisions.
                </p>
              </div>
            </div>
          </div>
        </section>

        <ValuesSection />
        <StatsSection />

        {/* CTA */}
        <section className="py-24 px-6">
          <div className="mx-auto max-w-4xl text-center">
            <div className="dark-card p-12">
              <h2 className="text-3xl font-bold text-white mb-4">Join Our Mission</h2>
              <p className="text-white/50 mb-8 max-w-xl mx-auto">
                Help us democratize business intelligence. Try PHOW today and see the difference data-driven decisions can make.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link
                  href="/app"
                  className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-xl bg-white text-black font-semibold text-lg hover:bg-white/90 transition-all"
                >
                  Get Started Free
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </Link>
                <a
                  href="mailto:hello@phow.ai"
                  className="inline-flex items-center justify-center px-8 py-4 rounded-xl bg-white/5 text-white font-semibold text-lg hover:bg-white/10 transition-all border border-white/10"
                >
                  Contact Us
                </a>
              </div>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}

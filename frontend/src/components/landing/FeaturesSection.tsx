"use client";

import { useIntersectionObserver } from "@/hooks/useIntersectionObserver";

const features = [
  {
    id: "location_scout",
    icon: "📍",
    name: "Location Scout",
    description: "Find the perfect location for your business with AI-powered analysis of foot traffic, demographics, and competition.",
    color: "from-sky-500 to-blue-600",
    capabilities: ["Foot traffic analysis", "Demographics", "Competition density", "Transit access"],
  },
  {
    id: "market_validator",
    icon: "📊",
    name: "Market Validator",
    description: "Validate your business idea with data-driven market research and demand analysis before you invest.",
    color: "from-violet-500 to-purple-600",
    capabilities: ["Market size", "Demand trends", "Growth potential", "Risk assessment"],
  },
  {
    id: "competitor_analyzer",
    icon: "🎯",
    name: "Competitor Analyzer",
    description: "Understand your competition with deep insights into their strategies, pricing, and customer reviews.",
    color: "from-orange-500 to-rose-600",
    capabilities: ["Competitor mapping", "Price analysis", "Review sentiment", "Market gaps"],
  },
  {
    id: "social_media_coach",
    icon: "💬",
    name: "Social Media Coach",
    description: "Get personalized social media strategies and content ideas tailored to your business and audience.",
    color: "from-pink-500 to-rose-500",
    capabilities: ["Content strategy", "Posting schedule", "Engagement tips", "Trend analysis"],
  },
];

export function FeaturesSection() {
  const { ref, isVisible } = useIntersectionObserver<HTMLElement>({ threshold: 0.1 });

  return (
    <section ref={ref} className="relative z-10 py-24 px-6">
      {/* Top gradient for seamless transition from hero */}
      <div
        className="absolute top-0 left-0 right-0 h-32 z-0"
        style={{
          background: "linear-gradient(to bottom, rgba(15, 23, 42, 0.95) 0%, transparent 100%)"
        }}
      />
      <div className="relative z-10 mx-auto max-w-6xl">
        {/* Section Header */}
        <div className={`text-center mb-16 animate-on-scroll ${isVisible ? "visible" : ""}`}>
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Everything You Need to Succeed
          </h2>
          <p className="text-lg text-white/60 max-w-2xl mx-auto">
            Powerful AI tools designed specifically for small business owners.
            Get insights that used to require expensive consultants.
          </p>
        </div>

        {/* Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {features.map((feature, index) => (
            <div
              key={feature.id}
              className={`glass-card p-8 group animate-on-scroll ${isVisible ? "visible" : ""}`}
              style={{ transitionDelay: `${(index + 1) * 100}ms` }}
            >
              {/* Icon */}
              <div className={`w-16 h-16 rounded-2xl flex items-center justify-center text-4xl mb-6 bg-gradient-to-br ${feature.color} shadow-lg group-hover:scale-110 transition-transform duration-300`}>
                {feature.icon}
              </div>

              {/* Content */}
              <h3 className="text-xl font-semibold text-white mb-3">{feature.name}</h3>
              <p className="text-white/60 mb-6">{feature.description}</p>

              {/* Capabilities */}
              <div className="flex flex-wrap gap-2">
                {feature.capabilities.map((cap) => (
                  <span
                    key={cap}
                    className="text-xs px-3 py-1 rounded-full bg-white/10 text-white/70"
                  >
                    {cap}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

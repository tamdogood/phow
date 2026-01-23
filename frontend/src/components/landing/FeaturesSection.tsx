"use client";

import { useIntersectionObserver } from "@/hooks/useIntersectionObserver";

const features = [
  {
    id: "location_scout",
    step: 1,
    name: "Choose a Location",
    description: "Enter any address and get instant AI analysis of foot traffic, demographics, and competition density.",
    color: "#3B82F6",
  },
  {
    id: "market_validator",
    step: 2,
    name: "Validate Your Market",
    description: "Understand market size, demand trends, and growth potential before making investment decisions.",
    color: "#8B5CF6",
  },
  {
    id: "competitor_analyzer",
    step: 3,
    name: "Analyze Competitors",
    description: "Get deep insights into competitor strategies, pricing, and customer reviews to find market gaps.",
    color: "#F97316",
  },
  {
    id: "get_insights",
    step: 4,
    name: "Get AI Insights",
    description: "Receive personalized recommendations and actionable insights powered by advanced AI analysis.",
    color: "#22C55E",
  },
];

export function FeaturesSection() {
  const { ref, isVisible } = useIntersectionObserver<HTMLElement>({ threshold: 0.1 });

  return (
    <section ref={ref} className="relative z-10 py-24 px-6">
      <div className="relative z-10 mx-auto max-w-6xl">
        {/* Section Header */}
        <div className={`text-center mb-16 animate-on-scroll ${isVisible ? "visible" : ""}`}>
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            How It Works
          </h2>
          <p className="text-lg text-white/50 max-w-2xl mx-auto">
            Four simple steps to smarter business decisions.
          </p>
        </div>

        {/* Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {features.map((feature, index) => (
            <div
              key={feature.id}
              className={`relative p-8 rounded-xl bg-[#111] border border-white/5 hover:border-white/10 transition-all animate-on-scroll ${isVisible ? "visible" : ""}`}
              style={{ transitionDelay: `${(index + 1) * 100}ms` }}
            >
              {/* Step Number */}
              <div
                className="w-10 h-10 rounded-full flex items-center justify-center text-lg font-bold mb-6"
                style={{ backgroundColor: `${feature.color}20`, color: feature.color }}
              >
                {feature.step}
              </div>

              {/* Content */}
              <h3 className="text-xl font-semibold text-white mb-3">{feature.name}</h3>
              <p className="text-white/50 leading-relaxed">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

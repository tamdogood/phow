"use client";

import Link from "next/link";
import { Header, Footer } from "@/components/landing";
import { useIntersectionObserver } from "@/hooks/useIntersectionObserver";

const tools = [
  {
    id: "location_scout",
    icon: "📍",
    name: "Location Scout",
    tagline: "Find Your Perfect Business Location",
    description: "Our AI-powered Location Scout analyzes foot traffic patterns, demographic data, competition density, and transit accessibility to help you find the ideal spot for your business.",
    color: "blue",
    features: [
      { title: "Foot Traffic Analysis", description: "Understand pedestrian patterns and peak hours in your target area." },
      { title: "Demographics Insights", description: "Get detailed breakdowns of age, income, and lifestyle data for any location." },
      { title: "Competition Mapping", description: "See exactly where competitors are located and identify market gaps." },
      { title: "Transit Accessibility", description: "Evaluate public transit options and parking availability." },
      { title: "Rent vs. Revenue Analysis", description: "Compare rent costs against projected revenue potential." },
      { title: "AI Recommendations", description: "Get personalized location suggestions based on your business type." },
    ],
  },
  {
    id: "market_validator",
    icon: "📊",
    name: "Market Validator",
    tagline: "Validate Your Business Idea with Data",
    description: "Before you invest, let our Market Validator analyze market size, demand trends, growth potential, and risk factors to ensure your business idea has real potential.",
    color: "purple",
    features: [
      { title: "Market Size Estimation", description: "Understand the total addressable market for your business idea." },
      { title: "Demand Trend Analysis", description: "See how demand has changed over time and where it's heading." },
      { title: "Growth Potential Score", description: "Get a data-driven score for your market's growth trajectory." },
      { title: "Risk Assessment", description: "Identify potential risks and challenges before they impact your business." },
      { title: "Target Customer Profiling", description: "Understand who your ideal customers are and how to reach them." },
      { title: "Revenue Projections", description: "Get realistic revenue estimates based on market data." },
    ],
  },
  {
    id: "competitor_analyzer",
    icon: "🎯",
    name: "Competitor Analyzer",
    tagline: "Know Your Competition Inside Out",
    description: "Gain deep insights into your competitors' strategies, pricing, customer reviews, and market positioning to find your competitive advantage.",
    color: "orange",
    features: [
      { title: "Competitor Discovery", description: "Automatically find and track all relevant competitors in your market." },
      { title: "Price Analysis", description: "Compare pricing strategies and find optimal price points." },
      { title: "Review Sentiment", description: "Analyze customer reviews to understand competitor strengths and weaknesses." },
      { title: "Market Gap Identification", description: "Discover underserved niches and unmet customer needs." },
      { title: "SWOT Analysis", description: "Get comprehensive strength, weakness, opportunity, and threat analysis." },
      { title: "Positioning Strategy", description: "Develop a unique positioning that sets you apart from competitors." },
    ],
  },
  {
    id: "social_media_coach",
    icon: "💬",
    name: "Social Media Coach",
    tagline: "Build Your Online Presence",
    description: "Get personalized social media strategies, content ideas, and posting schedules tailored to your business type and target audience.",
    color: "pink",
    features: [
      { title: "Content Strategy", description: "Develop a content plan that resonates with your audience." },
      { title: "Optimal Posting Schedule", description: "Know exactly when to post for maximum engagement." },
      { title: "Engagement Tips", description: "Learn techniques to boost likes, comments, and shares." },
      { title: "Trend Analysis", description: "Stay ahead with insights on trending topics in your industry." },
      { title: "Platform Recommendations", description: "Focus on the platforms that matter most for your business." },
      { title: "Content Ideas", description: "Get AI-generated content ideas tailored to your brand." },
    ],
  },
];

const colorClasses: Record<string, { bg: string; text: string; border: string }> = {
  blue: { bg: "bg-blue-500/20", text: "text-blue-400", border: "border-blue-500/30" },
  purple: { bg: "bg-purple-500/20", text: "text-purple-400", border: "border-purple-500/30" },
  orange: { bg: "bg-orange-500/20", text: "text-orange-400", border: "border-orange-500/30" },
  pink: { bg: "bg-pink-500/20", text: "text-pink-400", border: "border-pink-500/30" },
};

function ToolSection({ tool, index }: { tool: typeof tools[0]; index: number }) {
  const { ref, isVisible } = useIntersectionObserver<HTMLElement>({ threshold: 0.1 });
  const isEven = index % 2 === 0;
  const colors = colorClasses[tool.color];

  return (
    <section ref={ref} className={`py-24 px-6 ${index > 0 ? "border-t border-white/5" : ""}`}>
      <div className="mx-auto max-w-6xl">
        <div className={`grid grid-cols-1 lg:grid-cols-2 gap-12 items-center ${!isEven ? "lg:flex-row-reverse" : ""}`}>
          {/* Content */}
          <div className={`animate-on-scroll ${isVisible ? "visible" : ""} ${!isEven ? "lg:order-2" : ""}`}>
            {/* Icon */}
            <div className={`w-20 h-20 rounded-2xl flex items-center justify-center text-5xl mb-6 ${colors.bg}`}>
              {tool.icon}
            </div>

            <h2 className="text-3xl md:text-4xl font-bold text-white mb-2">{tool.name}</h2>
            <p className={`text-xl ${colors.text} mb-4`}>{tool.tagline}</p>
            <p className="text-white/50 mb-8 text-lg">{tool.description}</p>

            <Link
              href="/app"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-white text-black font-semibold hover:bg-white/90 transition-all"
            >
              Try {tool.name}
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          </div>

          {/* Features Grid */}
          <div className={`grid grid-cols-1 sm:grid-cols-2 gap-4 ${!isEven ? "lg:order-1" : ""}`}>
            {tool.features.map((feature, idx) => (
              <div
                key={feature.title}
                className={`dark-card p-5 hover-lift animate-on-scroll ${isVisible ? "visible" : ""}`}
                style={{ transitionDelay: `${(idx + 1) * 100}ms` }}
              >
                <h4 className="text-white font-medium mb-2">{feature.title}</h4>
                <p className="text-white/50 text-sm">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

export default function FeaturesPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] relative overflow-hidden">
      {/* Grid pattern overlay */}
      <div className="fixed inset-0 grid-pattern pointer-events-none" />

      <Header />

      <main className="relative z-10 pt-32">
        {/* Page Header */}
        <div className="text-center px-6 mb-16 animate-fade-in-up">
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-4 tracking-tight">
            Powerful AI Tools for Your <span className="text-accent-blue">Business</span>
          </h1>
          <p className="text-lg text-white/50 max-w-2xl mx-auto">
            Everything you need to research, validate, and grow your small business—powered by artificial intelligence.
          </p>
        </div>

        {/* Tool Sections */}
        {tools.map((tool, index) => (
          <ToolSection key={tool.id} tool={tool} index={index} />
        ))}

        {/* CTA */}
        <section className="py-24 px-6">
          <div className="mx-auto max-w-4xl text-center">
            <div className="dark-card p-12">
              <h2 className="text-3xl font-bold text-white mb-4">Ready to Get Started?</h2>
              <p className="text-white/50 mb-8 max-w-xl mx-auto">
                All tools are free to use during our beta period. Start making data-driven decisions today.
              </p>
              <Link
                href="/app"
                className="inline-flex items-center gap-2 px-8 py-4 rounded-xl bg-white text-black font-semibold text-lg hover:bg-white/90 transition-all"
              >
                Try All Tools Free
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </Link>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}

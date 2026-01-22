"use client";

import { useIntersectionObserver } from "@/hooks/useIntersectionObserver";

const steps = [
  {
    number: 1,
    title: "Choose a Tool",
    description: "Select from our suite of AI-powered analytics tools based on what you need—location analysis, market validation, or competitor research.",
    icon: "🛠️",
  },
  {
    number: 2,
    title: "Describe Your Business",
    description: "Tell us about your business idea, target market, and goals. Our AI understands context and tailors insights to your specific situation.",
    icon: "💬",
  },
  {
    number: 3,
    title: "Get Actionable Insights",
    description: "Receive data-driven recommendations, visualizations, and step-by-step guidance to make confident business decisions.",
    icon: "✨",
  },
];

export function HowItWorksSection() {
  const { ref, isVisible } = useIntersectionObserver<HTMLElement>({ threshold: 0.1 });

  return (
    <section ref={ref} className="relative z-10 py-24 px-6 bg-slate-900/30">
      <div className="mx-auto max-w-6xl">
        {/* Section Header */}
        <div className={`text-center mb-16 animate-on-scroll ${isVisible ? "visible" : ""}`}>
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            How It Works
          </h2>
          <p className="text-lg text-white/60 max-w-2xl mx-auto">
            Get started in minutes. No complex setup, no learning curve—just actionable insights.
          </p>
        </div>

        {/* Steps */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {steps.map((step, index) => (
            <div
              key={step.number}
              className={`relative text-center animate-on-scroll ${isVisible ? "visible" : ""}`}
              style={{ transitionDelay: `${(index + 1) * 150}ms` }}
            >
              {/* Connector Line (hidden on mobile and last item) */}
              {index < steps.length - 1 && (
                <div className="hidden md:block absolute top-12 left-[60%] w-[80%] h-px bg-gradient-to-r from-sky-500/50 to-transparent" />
              )}

              {/* Number Circle */}
              <div className="relative inline-flex items-center justify-center w-24 h-24 rounded-full bg-gradient-to-br from-sky-500/20 to-blue-600/20 border border-sky-500/30 mb-6">
                <span className="text-4xl">{step.icon}</span>
                <div className="absolute -top-2 -right-2 w-8 h-8 rounded-full bg-gradient-to-br from-sky-500 to-blue-600 flex items-center justify-center text-white font-bold text-sm shadow-lg shadow-sky-500/30">
                  {step.number}
                </div>
              </div>

              {/* Content */}
              <h3 className="text-xl font-semibold text-white mb-3">{step.title}</h3>
              <p className="text-white/60 max-w-xs mx-auto">{step.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

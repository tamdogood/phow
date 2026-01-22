"use client";

import { useIntersectionObserver } from "@/hooks/useIntersectionObserver";

const testimonials = [
  {
    quote: "PHOW helped me find the perfect location for my coffee shop. The foot traffic analysis was spot-on, and I'm now seeing 40% more customers than I projected.",
    author: "Sarah Chen",
    role: "Owner, Bean & Leaf Coffee",
    avatar: "SC",
    color: "from-sky-500 to-blue-600",
  },
  {
    quote: "Before launching my fitness studio, I used the Market Validator to understand demand. It saved me from opening in an oversaturated area.",
    author: "Marcus Johnson",
    role: "Founder, FitFlow Studio",
    avatar: "MJ",
    color: "from-violet-500 to-purple-600",
  },
  {
    quote: "The Competitor Analyzer showed me gaps in the local market I never knew existed. I positioned my bakery perfectly and hit profitability in month three.",
    author: "Emily Rodriguez",
    role: "Owner, Sweet Rise Bakery",
    avatar: "ER",
    color: "from-orange-500 to-rose-600",
  },
];

export function TestimonialsSection() {
  const { ref, isVisible } = useIntersectionObserver<HTMLElement>({ threshold: 0.1 });

  return (
    <section ref={ref} className="relative z-10 py-24 px-6">
      <div className="mx-auto max-w-6xl">
        {/* Section Header */}
        <div className={`text-center mb-16 animate-on-scroll ${isVisible ? "visible" : ""}`}>
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Loved by Business Owners
          </h2>
          <p className="text-lg text-white/60 max-w-2xl mx-auto">
            See how PHOW is helping entrepreneurs make smarter decisions every day.
          </p>
        </div>

        {/* Testimonial Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {testimonials.map((testimonial, index) => (
            <div
              key={testimonial.author}
              className={`glass-card p-8 animate-on-scroll ${isVisible ? "visible" : ""}`}
              style={{ transitionDelay: `${(index + 1) * 100}ms` }}
            >
              {/* Quote */}
              <div className="mb-6">
                <svg className="w-8 h-8 text-sky-500/30" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M14.017 21v-7.391c0-5.704 3.731-9.57 8.983-10.609l.995 2.151c-2.432.917-3.995 3.638-3.995 5.849h4v10h-9.983zm-14.017 0v-7.391c0-5.704 3.748-9.57 9-10.609l.996 2.151c-2.433.917-3.996 3.638-3.996 5.849h3.983v10h-9.983z" />
                </svg>
              </div>
              <p className="text-white/80 mb-6 leading-relaxed">{testimonial.quote}</p>

              {/* Author */}
              <div className="flex items-center gap-4">
                <div className={`w-12 h-12 rounded-full bg-gradient-to-br ${testimonial.color} flex items-center justify-center text-white font-semibold`}>
                  {testimonial.avatar}
                </div>
                <div>
                  <p className="text-white font-medium">{testimonial.author}</p>
                  <p className="text-white/50 text-sm">{testimonial.role}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

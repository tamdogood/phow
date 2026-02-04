"use client";

import dynamic from "next/dynamic";
import { useIntersectionObserver } from "@/hooks/useIntersectionObserver";

const HeroMapDemo = dynamic(
  () => import("./HeroMapDemo").then((mod) => mod.HeroMapDemo),
  {
    ssr: false,
    loading: () => <div className="w-full h-full bg-gray-100 animate-pulse" />,
  }
);

export function DemoSection() {
  const { ref, isVisible } = useIntersectionObserver<HTMLElement>({ threshold: 0.1 });

  return (
    <section id="demo" ref={ref} className="relative py-16 px-6">
      <div className="mx-auto max-w-6xl">
        <div className="relative">
          {/* Browser mockup frame */}
          <div
            className={`rounded-xl overflow-hidden border border-gray-200 bg-white shadow-2xl shadow-gray-200/50 animate-on-scroll ${isVisible ? "visible" : ""}`}
          >
            {/* Browser chrome */}
            <div className="flex items-center gap-2 px-4 py-3 bg-gray-50 border-b border-gray-100">
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-red-400" />
                <div className="w-3 h-3 rounded-full bg-yellow-400" />
                <div className="w-3 h-3 rounded-full bg-green-400" />
              </div>
              <div className="flex-1 mx-4">
                <div className="bg-white rounded px-3 py-1.5 text-sm text-gray-400 font-mono max-w-xs mx-auto text-center border border-gray-100">
                  phow.ai/app
                </div>
              </div>
              <div className="w-[52px]" />
            </div>
            {/* Map content */}
            <div className="h-[400px] md:h-[500px] relative">
              <HeroMapDemo />

              {/* Floating Widgets - Consistent 16px margin from edges, uniform sizing */}
              {/* Location Score Widget - Top Left */}
              <div
                className={`absolute top-4 left-4 bg-white/70 backdrop-blur-md border border-gray-200/50 rounded-xl p-4 w-44 shadow-lg shadow-black/5 animate-slide-in-left ${isVisible ? "" : "opacity-0"}`}
                style={{ animationDelay: "0.3s" }}
              >
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-7 h-7 rounded-lg bg-blue-500/10 flex items-center justify-center">
                    <svg className="w-3.5 h-3.5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                  </div>
                  <span className="text-gray-600 text-xs font-medium">Location Score</span>
                </div>
                <div className="flex items-end gap-2">
                  <span className="text-3xl font-bold text-gray-900">87</span>
                  <span className="text-green-500 text-xs mb-1">+12%</span>
                </div>
                <div className="mt-2 h-1 bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full w-[87%] bg-gradient-to-r from-blue-500 to-blue-400 rounded-full" />
                </div>
              </div>

              {/* Competitors Widget - Top Right */}
              <div
                className={`absolute top-4 right-4 bg-white/70 backdrop-blur-md border border-gray-200/50 rounded-xl p-4 w-44 shadow-lg shadow-black/5 animate-slide-in-right ${isVisible ? "" : "opacity-0"}`}
                style={{ animationDelay: "0.4s" }}
              >
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-7 h-7 rounded-lg bg-orange-500/10 flex items-center justify-center">
                    <svg className="w-3.5 h-3.5 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                  <span className="text-gray-600 text-xs font-medium">Competitors</span>
                </div>
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-500 text-xs">Within 0.5mi</span>
                    <span className="text-gray-900 font-semibold text-sm">12</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-500 text-xs">Avg Rating</span>
                    <span className="text-amber-500 font-semibold text-sm flex items-center gap-1">
                      4.2
                      <svg className="w-2.5 h-2.5" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-500 text-xs">Price Level</span>
                    <span className="text-green-500 font-semibold text-sm">$$</span>
                  </div>
                </div>
              </div>

              {/* Transit Score Widget - Bottom Left */}
              <div
                className={`absolute bottom-4 left-4 bg-white/70 backdrop-blur-md border border-gray-200/50 rounded-xl p-4 w-44 shadow-lg shadow-black/5 animate-slide-in-left ${isVisible ? "" : "opacity-0"}`}
                style={{ animationDelay: "0.5s" }}
              >
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-7 h-7 rounded-lg bg-green-500/10 flex items-center justify-center">
                    <svg className="w-3.5 h-3.5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                    </svg>
                  </div>
                  <span className="text-gray-600 text-xs font-medium">Transit Access</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-2xl font-bold text-green-500">A+</span>
                  <div className="text-xs text-gray-500">
                    <div>2 BART stations</div>
                    <div>5 bus lines</div>
                  </div>
                </div>
              </div>

              {/* Demographics Widget - Bottom Right */}
              <div
                className={`absolute bottom-4 right-4 bg-white/70 backdrop-blur-md border border-gray-200/50 rounded-xl p-4 w-44 shadow-lg shadow-black/5 animate-slide-in-right ${isVisible ? "" : "opacity-0"}`}
                style={{ animationDelay: "0.6s" }}
              >
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-7 h-7 rounded-lg bg-purple-500/10 flex items-center justify-center">
                    <svg className="w-3.5 h-3.5 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                    </svg>
                  </div>
                  <span className="text-gray-600 text-xs font-medium">Demographics</span>
                </div>
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-500 text-xs">Foot Traffic</span>
                    <span className="text-gray-900 font-semibold text-sm">High</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-500 text-xs">Median Income</span>
                    <span className="text-gray-900 font-semibold text-sm">$95K</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-500 text-xs">Age Group</span>
                    <span className="text-gray-900 font-semibold text-sm">25-44</span>
                  </div>
                </div>
              </div>

              {/* AI Insight Banner */}
              <div
                className={`absolute bottom-20 left-1/2 -translate-x-1/2 bg-white/80 backdrop-blur-md border border-gray-200/50 rounded-full px-4 py-2 shadow-lg shadow-black/5 animate-fade-in-up ${isVisible ? "" : "opacity-0"}`}
                style={{ animationDelay: "0.7s" }}
              >
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4 text-blue-500 animate-pulse" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                  <span className="text-gray-700 text-sm font-medium">
                    AI: This location scores 23% above area average
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Caption */}
        <p className="text-center text-gray-400 text-sm mt-6 font-mono">
          Location Scout - Analyze any address with AI-powered insights
        </p>
      </div>
    </section>
  );
}

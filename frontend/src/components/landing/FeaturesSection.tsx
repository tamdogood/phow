"use client";

import React, { useRef, useState, useEffect, useCallback } from "react";

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
  const [activeIndex, setActiveIndex] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const isDragging = useRef(false);
  const startX = useRef(0);
  const scrollStartX = useRef(0);

  const handlePrev = useCallback(() => {
    setActiveIndex((prev) => (prev - 1 + features.length) % features.length);
  }, []);

  const handleNext = useCallback(() => {
    setActiveIndex((prev) => (prev + 1) % features.length);
  }, []);

  // Handle wheel scroll within the section (horizontal scroll)
  const handleWheel = useCallback((e: WheelEvent) => {
    // Prevent default only if scrolling horizontally or if deltaY is significant
    if (Math.abs(e.deltaX) > Math.abs(e.deltaY) || Math.abs(e.deltaY) > 30) {
      e.preventDefault();

      const delta = e.deltaX !== 0 ? e.deltaX : e.deltaY;

      if (delta > 30) {
        handleNext();
      } else if (delta < -30) {
        handlePrev();
      }
    }
  }, [handleNext, handlePrev]);

  // Touch/drag handling for mobile
  const handlePointerDown = useCallback((e: React.PointerEvent) => {
    isDragging.current = true;
    startX.current = e.clientX;
    scrollStartX.current = activeIndex;
  }, [activeIndex]);

  const handlePointerMove = useCallback((e: React.PointerEvent) => {
    if (!isDragging.current) return;

    const diff = startX.current - e.clientX;
    // Visual feedback could be added here
  }, []);

  const handlePointerUp = useCallback((e: React.PointerEvent) => {
    if (!isDragging.current) return;
    isDragging.current = false;

    const diff = startX.current - e.clientX;
    const threshold = 50;

    if (diff > threshold) {
      handleNext();
    } else if (diff < -threshold) {
      handlePrev();
    }
  }, [handleNext, handlePrev]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "ArrowLeft") {
        handlePrev();
      } else if (e.key === "ArrowRight") {
        handleNext();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleNext, handlePrev]);

  // Attach wheel listener with passive: false to allow preventDefault
  useEffect(() => {
    const container = containerRef.current;
    if (container) {
      container.addEventListener("wheel", handleWheel, { passive: false });
      return () => container.removeEventListener("wheel", handleWheel);
    }
  }, [handleWheel]);

  // Get card position and style based on its index relative to active
  const getCardStyle = (index: number): React.CSSProperties => {
    // Calculate position relative to active (with wrapping for circular effect)
    let relativePos = index - activeIndex;

    // Handle wrapping for circular carousel
    if (relativePos > features.length / 2) {
      relativePos -= features.length;
    } else if (relativePos < -features.length / 2) {
      relativePos += features.length;
    }

    const isCenter = relativePos === 0;
    const isAdjacent = Math.abs(relativePos) === 1;
    const isVisible = Math.abs(relativePos) <= 2;

    // Calculate transform
    const translateX = relativePos * 320; // Card width + gap
    const scale = isCenter ? 1 : isAdjacent ? 0.85 : 0.7;
    const opacity = isCenter ? 1 : isAdjacent ? 0.5 : 0.2;
    const zIndex = isCenter ? 30 : isAdjacent ? 20 : 10;

    return {
      transform: `translateX(${translateX}px) scale(${scale})`,
      opacity: isVisible ? opacity : 0,
      zIndex,
      transition: "all 0.4s cubic-bezier(0.4, 0, 0.2, 1)",
      pointerEvents: isCenter ? "auto" : "none",
    };
  };

  return (
    <section className="relative z-10 py-24 px-6 overflow-hidden">
      <div className="mx-auto max-w-6xl">
        {/* Section Header */}
        <div className="text-center mb-8">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
            How It Works
          </h2>
          <p className="text-lg text-gray-500 max-w-2xl mx-auto">
            Four simple steps to smarter business decisions.
          </p>
        </div>

        {/* Carousel Container */}
        <div
          ref={containerRef}
          className="relative h-80 flex items-center justify-center cursor-grab active:cursor-grabbing select-none"
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerLeave={handlePointerUp}
        >
          {/* Gradient Overlays for fade effect on edges */}
          <div className="absolute left-0 top-0 bottom-0 w-32 bg-gradient-to-r from-white to-transparent z-40 pointer-events-none" />
          <div className="absolute right-0 top-0 bottom-0 w-32 bg-gradient-to-l from-white to-transparent z-40 pointer-events-none" />

          {/* Cards */}
          {features.map((feature, index) => (
            <div
              key={feature.id}
              className="absolute w-72 md:w-80 p-8 rounded-2xl bg-white border border-gray-100 shadow-lg"
              style={getCardStyle(index)}
            >
              {/* Step Number */}
              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center text-xl font-bold mb-6"
                style={{ backgroundColor: `${feature.color}15`, color: feature.color }}
              >
                {feature.step}
              </div>

              {/* Content */}
              <h3 className="text-xl font-semibold text-gray-900 mb-3">{feature.name}</h3>
              <p className="text-gray-500 leading-relaxed text-sm md:text-base">{feature.description}</p>
            </div>
          ))}
        </div>

        {/* Navigation */}
        <div className="flex items-center justify-center gap-6 mt-8">
          {/* Prev Button */}
          <button
            onClick={handlePrev}
            className="w-10 h-10 rounded-full bg-white border border-gray-200 shadow-sm flex items-center justify-center text-gray-600 hover:bg-gray-50 hover:border-gray-300 transition-all"
            aria-label="Previous"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>

          {/* Dots */}
          <div className="flex items-center gap-2">
            {features.map((feature, index) => (
              <button
                key={feature.id}
                onClick={() => setActiveIndex(index)}
                className="relative h-2 rounded-full overflow-hidden transition-all duration-300"
                style={{
                  width: index === activeIndex ? "32px" : "8px",
                  backgroundColor: index === activeIndex ? feature.color : "rgba(0,0,0,0.15)"
                }}
                aria-label={`Go to step ${index + 1}`}
              />
            ))}
          </div>

          {/* Next Button */}
          <button
            onClick={handleNext}
            className="w-10 h-10 rounded-full bg-white border border-gray-200 shadow-sm flex items-center justify-center text-gray-600 hover:bg-gray-50 hover:border-gray-300 transition-all"
            aria-label="Next"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>

        {/* Instruction */}
        <p className="text-center text-gray-400 text-sm mt-4 font-mono">
          Drag or use arrow keys to navigate
        </p>
      </div>
    </section>
  );
}

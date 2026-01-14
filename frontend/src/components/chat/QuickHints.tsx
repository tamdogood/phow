"use client";

import { useState } from "react";

interface QuickHintsProps {
  toolId: string;
  onSelectHint: (hint: string) => void;
  disabled?: boolean;
  hints?: string[];  // Hints from API, falls back to defaults if not provided
}

// Fallback hints if API doesn't provide them
const DEFAULT_HINTS: Record<string, string[]> = {
  location_scout: [
    "Analyze 100 Broadway, New York for a coffee shop",
    "What's near Pike Place Market in Seattle?",
    "Is there good transit access at 500 Market St, San Francisco?",
  ],
  market_validator: [
    "Is a gym viable at 200 Main St, Austin TX?",
    "Validate a bakery concept for downtown Portland",
    "What demographics support a pet store in Brooklyn?",
  ],
  competitor_analyzer: [
    "Find restaurant competitors near Times Square",
    "Analyze coffee shop competition in Capitol Hill, Seattle",
    "Show me the market positioning for gyms in Miami Beach",
  ],
  social_media_coach: [
    "What should I post today for my coffee shop in Austin?",
    "Give me content ideas for my restaurant this week",
    "What hashtags should I use for my bakery in Seattle?",
  ],
};

export function QuickHints({ toolId, onSelectHint, disabled, hints }: QuickHintsProps) {
  const [showMore, setShowMore] = useState(false);

  // Use provided hints or fall back to defaults
  const examples = hints && hints.length > 0
    ? hints
    : (DEFAULT_HINTS[toolId] || DEFAULT_HINTS.location_scout);

  // Show first 3 examples by default
  const visibleExamples = showMore ? examples : examples.slice(0, 3);

  return (
    <div className="w-full">
      {/* Example queries as subtle chips */}
      <div className="flex flex-wrap gap-2 justify-center">
        {visibleExamples.map((example, idx) => (
          <button
            key={idx}
            onClick={() => onSelectHint(example)}
            disabled={disabled}
            className={`
              group relative px-3 py-1.5 text-xs rounded-full border transition-all duration-200
              ${disabled
                ? "border-slate-700/60 text-slate-500 cursor-not-allowed"
                : "border-slate-600/60 text-slate-400 hover:border-sky-400/50 hover:text-sky-400 hover:bg-sky-400/10"
              }
            `}
          >
            <span className="flex items-center gap-1.5">
              <svg
                className={`w-3 h-3 ${disabled ? "text-slate-600" : "text-slate-500 group-hover:text-sky-400"}`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              {example}
            </span>
          </button>
        ))}
      </div>

      {/* Show more/less toggle */}
      {examples.length > 3 && (
        <button
          onClick={() => setShowMore(!showMore)}
          disabled={disabled}
          className={`
            mt-2 text-xs transition-colors mx-auto block
            ${disabled ? "text-slate-600" : "text-slate-500 hover:text-white"}
          `}
        >
          {showMore ? "Show less" : `+${examples.length - 3} more examples`}
        </button>
      )}
    </div>
  );
}

// Compact version for inline use
export function InlineHint({
  text,
  onClick,
  disabled
}: {
  text: string;
  onClick: () => void;
  disabled?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`
        inline-flex items-center gap-1 px-2 py-1 text-xs rounded-md transition-all
        ${disabled
          ? "bg-slate-800/60 text-slate-500 cursor-not-allowed"
          : "bg-slate-800/60 text-slate-400 hover:bg-sky-400/10 hover:text-sky-400"
        }
      `}
    >
      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
      {text}
    </button>
  );
}

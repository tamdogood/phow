"use client";

import { useState } from "react";

interface QuickHintsProps {
  toolId: string;
  onSelectHint: (hint: string) => void;
  disabled?: boolean;
}

// Hints organized by tool and category
const TOOL_HINTS: Record<string, {
  quickStart: string[];
  advanced: string[];
}> = {
  location_scout: {
    quickStart: [
      "Analyze [address] for a [business type]",
      "What's the foot traffic like at [address]?",
      "Show me competitors near [address]",
    ],
    advanced: [
      "Compare transit access between [address1] and [address2]",
      "What businesses are thriving in [neighborhood]?",
    ],
  },
  market_validator: {
    quickStart: [
      "Is [business type] viable at [address]?",
      "Validate the market for [business] in [city]",
      "What's the demographic profile near [address]?",
    ],
    advanced: [
      "What are the risks of opening [business] at [address]?",
      "Compare viability scores for [address1] vs [address2]",
    ],
  },
  competitor_analyzer: {
    quickStart: [
      "Find competitors for [business] near [address]",
      "Who are the top-rated [business type] in [area]?",
      "Analyze reviews of competitors near [address]",
    ],
    advanced: [
      "Create a positioning map for [business type] in [area]",
      "What gaps exist in the [business] market near [address]?",
    ],
  },
};

// Concrete example hints per tool (ready to use)
const EXAMPLE_HINTS: Record<string, string[]> = {
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
};

export function QuickHints({ toolId, onSelectHint, disabled }: QuickHintsProps) {
  const [showMore, setShowMore] = useState(false);

  const hints = TOOL_HINTS[toolId] || TOOL_HINTS.location_scout;
  const examples = EXAMPLE_HINTS[toolId] || EXAMPLE_HINTS.location_scout;

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
              group relative px-3 py-1.5 text-xs rounded-full border transition-all duration-150
              ${disabled
                ? "border-gray-200 text-gray-400 cursor-not-allowed"
                : "border-gray-200 text-gray-600 hover:border-blue-300 hover:text-blue-600 hover:bg-blue-50"
              }
            `}
          >
            <span className="flex items-center gap-1.5">
              <svg
                className={`w-3 h-3 ${disabled ? "text-gray-300" : "text-gray-400 group-hover:text-blue-500"}`}
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
            ${disabled ? "text-gray-300" : "text-gray-400 hover:text-gray-600"}
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
          ? "bg-gray-100 text-gray-400 cursor-not-allowed"
          : "bg-gray-100 text-gray-600 hover:bg-blue-100 hover:text-blue-700"
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

"use client";

import { useState, useEffect } from "react";

interface Tool {
  id: string;
  name: string;
  description: string;
  icon: string;
}

interface ToolSelectorProps {
  onSelectTool: (toolId: string) => void;
  selectedToolId?: string;
}

// Tool metadata with examples and capabilities
const TOOL_METADATA: Record<string, {
  tagline: string;
  examples: string[];
  capabilities: string[];
  color: string;
}> = {
  location_scout: {
    tagline: "Find the perfect spot for your business",
    examples: [
      "Is 123 Main St, Austin TX good for a coffee shop?",
      "Analyze the neighborhood around Pike Place Market for a bakery",
    ],
    capabilities: ["Competition mapping", "Transit access", "Foot traffic analysis"],
    color: "from-blue-500 to-cyan-500",
  },
  market_validator: {
    tagline: "Validate your business idea with real data",
    examples: [
      "Is a gym viable at 456 Oak Ave, Seattle?",
      "Validate the market for a pet store in downtown Portland",
    ],
    capabilities: ["Demographics analysis", "Market sizing", "Viability scoring"],
    color: "from-indigo-500 to-purple-500",
  },
  competitor_analyzer: {
    tagline: "Understand your competition deeply",
    examples: [
      "Who are my competitors for a restaurant near Union Square?",
      "Analyze coffee shop competition in Brooklyn Heights",
    ],
    capabilities: ["Competitor profiling", "Review analysis", "Market positioning"],
    color: "from-orange-500 to-red-500",
  },
};

export function ToolSelector({ onSelectTool, selectedToolId }: ToolSelectorProps) {
  const [tools, setTools] = useState<Tool[]>([]);
  const [loading, setLoading] = useState(true);
  const [hoveredTool, setHoveredTool] = useState<string | null>(null);

  useEffect(() => {
    async function fetchTools() {
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/tools`
        );
        if (response.ok) {
          const data = await response.json();
          setTools(data);
        }
      } catch (error) {
        console.error("Failed to fetch tools:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchTools();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        <p className="mt-4 text-sm text-gray-500">Loading tools...</p>
      </div>
    );
  }

  return (
    <div className="w-full max-w-4xl mx-auto">
      {/* Header */}
      <div className="text-center mb-8">
        <h2 className="text-2xl font-semibold text-gray-900 mb-2">
          How can I help your business today?
        </h2>
        <p className="text-gray-500">
          Choose a tool to get started with AI-powered insights
        </p>
      </div>

      {/* Tool Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {tools.map((tool) => {
          const metadata = TOOL_METADATA[tool.id] || {
            tagline: tool.description,
            examples: [],
            capabilities: [],
            color: "from-gray-500 to-gray-600",
          };
          const isSelected = selectedToolId === tool.id;
          const isHovered = hoveredTool === tool.id;

          return (
            <button
              key={tool.id}
              onClick={() => onSelectTool(tool.id)}
              onMouseEnter={() => setHoveredTool(tool.id)}
              onMouseLeave={() => setHoveredTool(null)}
              className={`
                relative group text-left p-5 rounded-xl border-2 transition-all duration-200
                ${isSelected
                  ? "border-blue-500 bg-blue-50 shadow-md"
                  : "border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm"
                }
              `}
            >
              {/* Icon */}
              <div className={`
                w-12 h-12 rounded-lg flex items-center justify-center text-2xl mb-3
                bg-gradient-to-br ${metadata.color} text-white
              `}>
                {tool.icon}
              </div>

              {/* Title */}
              <h3 className="font-semibold text-gray-900 mb-1">{tool.name}</h3>

              {/* Tagline */}
              <p className="text-sm text-gray-500 mb-3">{metadata.tagline}</p>

              {/* Capabilities (show on hover) */}
              <div className={`
                transition-all duration-200 overflow-hidden
                ${isHovered || isSelected ? "max-h-24 opacity-100" : "max-h-0 opacity-0"}
              `}>
                <div className="flex flex-wrap gap-1.5 pt-2 border-t border-gray-100">
                  {metadata.capabilities.map((cap, idx) => (
                    <span
                      key={idx}
                      className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600"
                    >
                      {cap}
                    </span>
                  ))}
                </div>
              </div>

              {/* Selected indicator */}
              {isSelected && (
                <div className="absolute top-3 right-3">
                  <div className="w-5 h-5 rounded-full bg-blue-500 flex items-center justify-center">
                    <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Quick tip */}
      <p className="text-center text-xs text-gray-400 mt-6">
        Tip: You can switch between tools anytime during your session
      </p>
    </div>
  );
}

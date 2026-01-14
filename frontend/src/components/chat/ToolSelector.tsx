"use client";

import { useState, useEffect } from "react";

interface Tool {
  id: string;
  name: string;
  description: string;
  icon: string;
  hints?: string[];
  capabilities?: string[];
}

interface ToolSelectorProps {
  onSelectTool: (toolId: string) => void;
  selectedToolId?: string;
}

// Gradient colors per tool for visual distinction
const TOOL_COLORS: Record<string, string> = {
  location_scout: "from-blue-500 to-cyan-500",
  market_validator: "from-indigo-500 to-purple-500",
  competitor_analyzer: "from-orange-500 to-red-500",
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
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        <p className="mt-4 text-sm text-muted-foreground">Loading tools...</p>
      </div>
    );
  }

  return (
    <div className="w-full max-w-4xl mx-auto">
      {/* Header */}
      <div className="text-center mb-8">
        <h2 className="text-2xl font-semibold text-foreground mb-2">
          How can I help your business today?
        </h2>
        <p className="text-muted-foreground">
          Choose a tool to get started with AI-powered insights
        </p>
      </div>

      {/* Tool Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {tools.map((tool) => {
          const color = TOOL_COLORS[tool.id] || "from-gray-500 to-gray-600";
          const capabilities = tool.capabilities || [];
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
                  ? "border-primary bg-primary/10 shadow-md"
                  : "border-border bg-card hover:border-border/80 hover:shadow-sm"
                }
              `}
            >
              {/* Icon */}
              <div className={`
                w-12 h-12 rounded-lg flex items-center justify-center text-2xl mb-3
                bg-gradient-to-br ${color} text-white
              `}>
                {tool.icon}
              </div>

              {/* Title */}
              <h3 className="font-semibold text-foreground mb-1">{tool.name}</h3>

              {/* Description */}
              <p className="text-sm text-muted-foreground mb-3 line-clamp-2">{tool.description}</p>

              {/* Capabilities (show on hover) */}
              {capabilities.length > 0 && (
                <div className={`
                  transition-all duration-200 overflow-hidden
                  ${isHovered || isSelected ? "max-h-24 opacity-100" : "max-h-0 opacity-0"}
                `}>
                  <div className="flex flex-wrap gap-1.5 pt-2 border-t border-border/60">
                    {capabilities.map((cap, idx) => (
                      <span
                        key={idx}
                        className="text-xs px-2 py-0.5 rounded-full bg-muted/60 text-muted-foreground"
                      >
                        {cap}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Selected indicator */}
              {isSelected && (
                <div className="absolute top-3 right-3">
                  <div className="w-5 h-5 rounded-full bg-primary flex items-center justify-center">
                    <svg className="w-3 h-3 text-primary-foreground" fill="currentColor" viewBox="0 0 20 20">
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
      <p className="text-center text-xs text-muted-foreground mt-6">
        Tip: You can switch between tools anytime during your session
      </p>
    </div>
  );
}

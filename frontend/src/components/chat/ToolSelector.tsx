"use client";

import { useState, useEffect } from "react";
import { fetchTools } from "@/lib/api";

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
  location_scout: "from-sky-500 to-blue-600",
  market_validator: "from-violet-500 to-purple-600",
  competitor_analyzer: "from-orange-500 to-rose-600",
  social_media_coach: "from-pink-500 to-rose-500",
};

export function ToolSelector({ onSelectTool, selectedToolId }: ToolSelectorProps) {
  const [tools, setTools] = useState<Tool[]>([]);
  const [loading, setLoading] = useState(true);
  const [hoveredTool, setHoveredTool] = useState<string | null>(null);

  useEffect(() => {
    async function loadTools() {
      try {
        const data = await fetchTools();
        setTools(data);
      } catch (error) {
        console.error("Failed to fetch tools:", error);
      } finally {
        setLoading(false);
      }
    }
    loadTools();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <div className="w-8 h-8 border-2 border-sky-400 border-t-transparent rounded-full animate-spin" />
        <p className="mt-4 text-sm text-white/60">Loading tools...</p>
      </div>
    );
  }

  return (
    <div className="w-full">
      {/* Tool Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
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
                glass-card relative group text-left p-6 transition-all duration-300
                hover:scale-[1.02] hover:shadow-lg
                ${isSelected ? "ring-2 ring-sky-400 shadow-lg shadow-sky-400/20" : ""}
              `}
            >
              {/* Icon */}
              <div className={`
                w-14 h-14 rounded-xl flex items-center justify-center text-3xl mb-4
                bg-gradient-to-br ${color} text-white shadow-lg
                group-hover:scale-110 transition-transform duration-300
              `}>
                {tool.icon}
              </div>

              {/* Title */}
              <h3 className="font-semibold text-white text-lg mb-2">{tool.name}</h3>

              {/* Description */}
              <p className="text-sm text-slate-400 mb-4 line-clamp-2">{tool.description}</p>

              {/* Capabilities (show on hover) */}
              {capabilities.length > 0 && (
                <div className={`
                  transition-all duration-300 overflow-hidden
                  ${isHovered || isSelected ? "max-h-32 opacity-100" : "max-h-0 opacity-0"}
                `}>
                  <div className="flex flex-wrap gap-1.5 pt-3 border-t border-slate-700/50">
                    {capabilities.map((cap, idx) => (
                      <span
                        key={idx}
                        className="text-xs px-2 py-1 rounded-full bg-white/10 text-slate-300"
                      >
                        {cap}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Selected indicator */}
              {isSelected && (
                <div className="absolute top-4 right-4">
                  <div className="w-6 h-6 rounded-full bg-sky-500 flex items-center justify-center shadow-lg shadow-sky-500/50">
                    <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                </div>
              )}

              {/* Hover glow effect */}
              <div className={`
                absolute inset-0 rounded-2xl transition-opacity duration-300 pointer-events-none
                ${isHovered ? "opacity-100" : "opacity-0"}
              `} style={{
                background: "radial-gradient(circle at center, rgba(56, 189, 248, 0.1) 0%, transparent 70%)"
              }} />
            </button>
          );
        })}
      </div>

      {/* Quick tip */}
      <p className="text-center text-xs text-white/40 mt-8">
        Select a tool to start chatting with AI-powered insights
      </p>
    </div>
  );
}

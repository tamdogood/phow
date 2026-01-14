"use client";

import { useState, useEffect, useRef } from "react";

interface Tool {
  id: string;
  name: string;
  description: string;
  icon: string;
}

interface ToolBarProps {
  currentToolId: string;
  onSwitchTool: (toolId: string) => void;
}

export function ToolBar({ currentToolId, onSwitchTool }: ToolBarProps) {
  const [tools, setTools] = useState<Tool[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const currentTool = tools.find((t) => t.id === currentToolId);

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
      }
    }
    fetchTools();
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  if (!currentTool) return null;

  const otherTools = tools.filter((t) => t.id !== currentToolId);

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Current tool indicator */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-600/50 bg-slate-800/50 hover:bg-slate-700/50 transition-colors group"
      >
        <span className="text-lg">{currentTool.icon}</span>
        <div className="text-left">
          <div className="text-sm font-medium text-white">{currentTool.name}</div>
        </div>
        <svg
          className={`w-4 h-4 text-slate-400 transition-transform ${isOpen ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown */}
      {isOpen && otherTools.length > 0 && (
        <div className="absolute top-full right-0 mt-1 w-64 glass-card py-1 z-50 shadow-xl">
          <div className="px-3 py-2 text-xs text-slate-400 border-b border-slate-700/50">
            Switch to another tool
          </div>
          {otherTools.map((tool) => (
            <button
              key={tool.id}
              onClick={() => {
                onSwitchTool(tool.id);
                setIsOpen(false);
              }}
              className="w-full flex items-center gap-3 px-3 py-2 hover:bg-white/5 transition-colors"
            >
              <span className="text-lg">{tool.icon}</span>
              <div className="text-left">
                <div className="text-sm font-medium text-white">{tool.name}</div>
                <div className="text-xs text-slate-400 truncate">{tool.description}</div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// Compact pill version for the header
export function ToolPill({
  icon,
  name,
  onClick,
}: {
  icon: string;
  name: string;
  onClick?: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`
        inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-sm
        bg-slate-800/50 border border-slate-700/50
        ${onClick ? "hover:border-sky-400/50 hover:bg-slate-700/50 cursor-pointer" : "cursor-default"}
        transition-all
      `}
    >
      <span>{icon}</span>
      <span className="text-white font-medium">{name}</span>
    </button>
  );
}

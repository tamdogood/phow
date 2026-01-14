"use client";

import { useState, useEffect } from "react";
import dynamic from "next/dynamic";

const Chat = dynamic(() => import("@/components/chat").then((mod) => ({ default: mod.Chat })), {
  ssr: false,
});

const ToolSelector = dynamic(
  () => import("@/components/chat/ToolSelector").then((mod) => ({ default: mod.ToolSelector })),
  { ssr: false }
);

interface Tool {
  id: string;
  name: string;
  description: string;
  icon: string;
  hints?: string[];
  capabilities?: string[];
}

export default function Home() {
  const [selectedTool, setSelectedTool] = useState<Tool | null>(null);
  const [tools, setTools] = useState<Tool[]>([]);
  const [chatKey, setChatKey] = useState(0);

  // Fetch tools on mount
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

  const handleSelectTool = (toolId: string) => {
    const tool = tools.find((t) => t.id === toolId);
    if (tool) {
      setSelectedTool(tool);
      setChatKey((prev) => prev + 1);
    }
  };

  const handleSwitchTool = (toolId: string) => {
    const tool = tools.find((t) => t.id === toolId);
    if (tool) {
      setSelectedTool(tool);
      setChatKey((prev) => prev + 1);
    }
  };

  const handleReset = () => {
    setSelectedTool(null);
    setChatKey((prev) => prev + 1);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="flex min-h-screen flex-col bg-white">
      {/* Header */}
      <header className="border-b px-6 py-4">
        <div className="mx-auto max-w-4xl flex items-center justify-between">
          <button
            type="button"
            onClick={handleReset}
            className="text-left text-xl font-bold text-gray-900 hover:text-gray-700 transition-colors cursor-pointer"
            aria-label="Go to home and clear chat"
          >
            PHOW
          </button>
          <span className="text-sm text-gray-500">AI Business Analytics</span>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 mx-auto w-full max-w-4xl">
        {!selectedTool ? (
          <div className="flex items-center justify-center min-h-[calc(100vh-80px)] p-6">
            <ToolSelector onSelectTool={handleSelectTool} />
          </div>
        ) : (
          <Chat
            key={chatKey}
            toolId={selectedTool.id}
            toolName={selectedTool.name}
            toolDescription={selectedTool.description}
            toolIcon={selectedTool.icon}
            toolHints={selectedTool.hints}
            toolCapabilities={selectedTool.capabilities}
            onSwitchTool={handleSwitchTool}
          />
        )}
      </main>
    </div>
  );
}

"use client";

import { useState } from "react";
import dynamic from "next/dynamic";

const Chat = dynamic(() => import("@/components/chat").then((mod) => ({ default: mod.Chat })), {
  ssr: false,
});

export default function Home() {
  const [chatKey, setChatKey] = useState(0);

  const handleReset = () => {
    // Force Chat remount to clear local state (messages, streaming, etc.)
    setChatKey((prev) => prev + 1);
    // Scroll to top for a clean reset experience
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
        <Chat
          key={chatKey}
          toolId="location_scout"
          toolName="Location Scout"
          toolDescription="Analyze if a location is good for your business"
        />
      </main>
    </div>
  );
}

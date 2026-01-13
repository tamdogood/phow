"use client";

import { Chat } from "@/components/chat";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col bg-white">
      {/* Header */}
      <header className="border-b px-6 py-4">
        <div className="mx-auto max-w-4xl flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-900">PHOW</h1>
          <span className="text-sm text-gray-500">AI Business Analytics</span>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 mx-auto w-full max-w-4xl">
        <Chat
          toolId="location_scout"
          toolName="Location Scout"
          toolDescription="Analyze if a location is good for your business"
        />
      </main>
    </div>
  );
}

"use client";

import { useState, useEffect, useRef } from "react";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { QuickHints } from "./QuickHints";
import { ToolBar } from "./ToolBar";
import { sendChatMessage } from "@/lib/api";
import { getSessionId } from "@/lib/session";

interface ChatProps {
  toolId: string;
  toolName: string;
  toolDescription: string;
  toolIcon?: string;
  toolHints?: string[];
  toolCapabilities?: string[];
  onSwitchTool?: (toolId: string) => void;
}

interface LocalMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
}

// Tool-specific welcome content
const TOOL_WELCOME: Record<string, {
  greeting: string;
  description: string;
  capabilities: string[];
}> = {
  location_scout: {
    greeting: "Ready to scout locations",
    description: "I'll analyze neighborhoods, map competitors, and assess foot traffic for any address you're considering.",
    capabilities: [
      "Competition density mapping",
      "Transit accessibility check",
      "Foot traffic indicators",
      "Neighborhood overview",
    ],
  },
  market_validator: {
    greeting: "Let's validate your market",
    description: "I'll analyze demographics, assess competition saturation, and give you a viability score based on real data.",
    capabilities: [
      "Demographics analysis",
      "Market size estimation",
      "Competition saturation scoring",
      "Risk & opportunity assessment",
    ],
  },
  competitor_analyzer: {
    greeting: "Time to analyze the competition",
    description: "I'll find competitors, analyze their reviews, and help you identify gaps in the market.",
    capabilities: [
      "Competitor discovery",
      "Review sentiment analysis",
      "Price vs quality positioning",
      "Market gap identification",
    ],
  },
};

export function Chat({
  toolId,
  toolName,
  toolDescription,
  toolIcon,
  toolHints,
  toolCapabilities,
  onSwitchTool,
}: ChatProps) {
  const [messages, setMessages] = useState<LocalMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [streamingContent, setStreamingContent] = useState("");
  const [inputValue, setInputValue] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const defaultWelcome = TOOL_WELCOME[toolId] || {
    greeting: `Welcome to ${toolName}`,
    description: toolDescription,
    capabilities: [],
  };

  // Use API capabilities if provided, otherwise fall back to defaults
  const welcome = {
    ...defaultWelcome,
    capabilities: toolCapabilities && toolCapabilities.length > 0
      ? toolCapabilities
      : defaultWelcome.capabilities,
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingContent]);

  // Reset conversation when tool changes
  useEffect(() => {
    setMessages([]);
    setConversationId(null);
    setStreamingContent("");
  }, [toolId]);

  const handleSend = async (message: string) => {
    const sessionId = getSessionId();
    if (!sessionId) return;

    // Add user message
    const userMessage: LocalMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: message,
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setStreamingContent("");
    setInputValue("");

    // Stream the response
    let fullResponse = "";
    await sendChatMessage(sessionId, toolId, message, conversationId, {
      onChunk: (content) => {
        fullResponse += content;
        setStreamingContent(fullResponse);
      },
      onDone: (newConversationId) => {
        setConversationId(newConversationId);
        // Add the complete assistant message
        const assistantMessage: LocalMessage = {
          id: crypto.randomUUID(),
          role: "assistant",
          content: fullResponse,
        };
        setMessages((prev) => [...prev, assistantMessage]);
        setStreamingContent("");
        setIsLoading(false);
      },
      onError: (error) => {
        console.error("Chat error:", error);
        const errorMessage: LocalMessage = {
          id: crypto.randomUUID(),
          role: "assistant",
          content: `Error: ${error}. Please try again.`,
        };
        setMessages((prev) => [...prev, errorMessage]);
        setStreamingContent("");
        setIsLoading(false);
      },
    });
  };

  const handleHintSelect = (hint: string) => {
    setInputValue(hint);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b border-border/60 bg-card px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {toolIcon && (
              <div className="w-10 h-10 rounded-lg bg-primary flex items-center justify-center text-xl text-primary-foreground shadow-sm">
                {toolIcon}
              </div>
            )}
            <div>
              <h2 className="font-semibold text-foreground">{toolName}</h2>
              <p className="text-sm text-muted-foreground">{toolDescription}</p>
            </div>
          </div>
          {onSwitchTool && (
            <ToolBar currentToolId={toolId} onSwitchTool={onSwitchTool} />
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-muted/30">
        {/* Enhanced Welcome Message */}
        {messages.length === 0 && !isLoading && (
          <div className="max-w-2xl mx-auto">
            {/* Welcome card */}
            <div className="bg-card rounded-2xl shadow-sm border border-border/60 p-6 mb-6">
              <div className="text-center mb-6">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary text-3xl text-primary-foreground mb-4 shadow-sm">
                  {toolIcon || "🔍"}
                </div>
                <h3 className="text-xl font-semibold text-foreground mb-2">
                  {welcome.greeting}
                </h3>
                <p className="text-muted-foreground">{welcome.description}</p>
              </div>

              {/* Capabilities */}
              {welcome.capabilities.length > 0 && (
                <div className="grid grid-cols-2 gap-2 mb-6">
                  {welcome.capabilities.map((cap, idx) => (
                    <div
                      key={idx}
                      className="flex items-center gap-2 text-sm text-muted-foreground bg-muted/40 rounded-lg px-3 py-2"
                    >
                      <svg
                        className="w-4 h-4 text-primary flex-shrink-0"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                      {cap}
                    </div>
                  ))}
                </div>
              )}

              {/* Subtle divider */}
              <div className="relative my-4">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-border/60"></div>
                </div>
                <div className="relative flex justify-center text-xs">
                  <span className="bg-card px-3 text-muted-foreground">Try an example</span>
                </div>
              </div>

              {/* Quick hints */}
              <QuickHints
                toolId={toolId}
                onSelectHint={handleHintSelect}
                disabled={isLoading}
                hints={toolHints}
              />
            </div>
          </div>
        )}

        {/* Message list */}
        {messages.map((msg) => (
          <ChatMessage key={msg.id} role={msg.role} content={msg.content} />
        ))}

        {/* Streaming message */}
        {streamingContent && (
          <ChatMessage
            role="assistant"
            content={streamingContent}
            isStreaming={true}
          />
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="border-t border-border/60 bg-card p-4">
        {/* Quick hints when conversation is active but not loading */}
        {messages.length > 0 && !isLoading && (
          <div className="mb-3">
            <QuickHints
              toolId={toolId}
              onSelectHint={handleHintSelect}
              disabled={isLoading}
              hints={toolHints}
            />
          </div>
        )}

        <ChatInput
          onSend={handleSend}
          disabled={isLoading}
          placeholder={`Ask ${toolName.toLowerCase()} a question...`}
          value={inputValue}
          onChange={setInputValue}
        />
      </div>
    </div>
  );
}

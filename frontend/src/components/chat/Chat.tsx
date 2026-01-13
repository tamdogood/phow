"use client";

import { useState, useEffect, useRef } from "react";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { sendChatMessage } from "@/lib/api";
import { getSessionId } from "@/lib/session";
import { Message } from "@/types";

interface ChatProps {
  toolId: string;
  toolName: string;
  toolDescription: string;
}

interface LocalMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export function Chat({ toolId, toolName, toolDescription }: ChatProps) {
  const [messages, setMessages] = useState<LocalMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [streamingContent, setStreamingContent] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingContent]);

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

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b p-4">
        <h2 className="text-lg font-semibold">{toolName}</h2>
        <p className="text-sm text-gray-500">{toolDescription}</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && !isLoading && (
          <div className="text-center text-gray-500 py-8">
            <p className="text-lg mb-2">Welcome to {toolName}!</p>
            <p className="text-sm">
              Ask me about any location you&apos;re considering for your business.
            </p>
            <p className="text-sm mt-2 text-gray-400">
              Example: &quot;Is 123 Main St, Austin TX good for a coffee shop?&quot;
            </p>
          </div>
        )}

        {messages.map((msg) => (
          <ChatMessage key={msg.id} role={msg.role} content={msg.content} />
        ))}

        {streamingContent && (
          <ChatMessage
            role="assistant"
            content={streamingContent}
            isStreaming={true}
          />
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t p-4">
        <ChatInput
          onSend={handleSend}
          disabled={isLoading}
          placeholder="Ask about a location..."
        />
      </div>
    </div>
  );
}

"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import { ChatMessage } from "@/components/chat/ChatMessage";
import { ChatInput } from "@/components/chat/ChatInput";
import { sendChatMessage, fetchConversations } from "@/lib/api";
import { getSessionId } from "@/lib/session";
import { Conversation } from "@/types";

interface Tool {
  id: string;
  name: string;
  description: string;
  icon: string;
  hints?: string[];
}

interface LocalMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
}

const TOOL_COLORS: Record<string, string> = {
  location_scout: "from-sky-500 to-blue-600",
  market_validator: "from-violet-500 to-purple-600",
  competitor_analyzer: "from-orange-500 to-rose-600",
  social_media_coach: "from-pink-500 to-rose-500",
  review_responder: "from-emerald-500 to-teal-600",
};

const EXAMPLE_PROMPTS = [
  "Find the best location for my coffee shop in San Francisco",
  "Is there demand for a yoga studio in Austin?",
  "Who are my competitors for a bakery in downtown Seattle?",
  "Help me create social media content for my restaurant",
];

function detectTool(message: string): string {
  const lower = message.toLowerCase();
  if (lower.includes("review") || lower.includes("respond") || lower.includes("reply")) {
    return "review_responder";
  }
  if (lower.includes("social") || lower.includes("instagram") || lower.includes("marketing") || lower.includes("content") || lower.includes("post")) {
    return "social_media_coach";
  }
  if (lower.includes("competitor") || lower.includes("competition") || lower.includes("rivals") || lower.includes("competing")) {
    return "competitor_analyzer";
  }
  if (lower.includes("market") || lower.includes("demand") || lower.includes("validate") || lower.includes("viable") || lower.includes("viability")) {
    return "market_validator";
  }
  return "location_scout";
}

export default function AppPage() {
  const { user, loading: authLoading, isConfigured, signInWithGoogle } = useAuth();
  const [tools, setTools] = useState<Tool[]>([]);
  const [messages, setMessages] = useState<LocalMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [streamingContent, setStreamingContent] = useState("");
  const [inputValue, setInputValue] = useState("");
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [leftSidebarOpen, setLeftSidebarOpen] = useState(true);
  const [rightSidebarOpen, setRightSidebarOpen] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

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

  useEffect(() => {
    async function loadConversations() {
      if (!user) return;
      const sessionId = getSessionId();
      if (!sessionId) return;
      try {
        const convos = await fetchConversations(sessionId);
        setConversations(convos);
      } catch (error) {
        console.error("Failed to fetch conversations:", error);
      }
    }
    loadConversations();
  }, [user]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingContent]);

  const handleNewChat = () => {
    setMessages([]);
    setConversationId(null);
    setStreamingContent("");
    setInputValue("");
  };

  const handleSend = async (message: string) => {
    const sessionId = getSessionId();
    if (!sessionId) return;

    const detectedToolId = detectTool(message);
    const tool = tools.find((t) => t.id === detectedToolId) || tools[0];
    const toolId = tool?.id || "location_scout";

    const userMessage: LocalMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: message,
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setStreamingContent("");
    setInputValue("");

    let fullResponse = "";
    await sendChatMessage(sessionId, toolId, message, conversationId, {
      onChunk: (content) => {
        fullResponse += content;
        setStreamingContent(fullResponse);
      },
      onDone: (newConversationId) => {
        setConversationId(newConversationId);
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

  const handleExampleClick = (prompt: string) => {
    setInputValue(prompt);
  };

  const handleToolCardClick = (tool: Tool) => {
    const hint = tool.hints?.[0] || `Help me with ${tool.name.toLowerCase()}`;
    setInputValue(hint);
  };

  const handleCopyChat = () => {
    const text = messages.map((m) => `${m.role === "user" ? "You" : "Assistant"}: ${m.content}`).join("\n\n");
    navigator.clipboard.writeText(text);
  };

  const handleExportPDF = () => {
    // Basic print-to-PDF functionality
    window.print();
  };

  const hasMessages = messages.length > 0 || streamingContent;

  return (
    <div className="min-h-screen relative overflow-hidden flex flex-col">
      {/* Background */}
      <div
        className="fixed inset-0 z-0"
        style={{
          backgroundImage: `url('https://plus.unsplash.com/premium_photo-1664443577580-dd2674e9d359?q=80&w=2071&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D')`,
          backgroundSize: "cover",
          backgroundPosition: "center",
          backgroundRepeat: "no-repeat",
        }}
      />
      <div className="fixed inset-0 z-0 bg-gradient-to-b from-slate-900/60 via-slate-900/40 to-slate-900/80" />

      {/* Header - Matching landing page */}
      <header className="glass-header fixed top-0 left-0 right-0 z-50 px-6 py-4">
        <div className="mx-auto max-w-6xl flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link href="/" className="text-2xl font-bold text-white hover:text-white/80 transition-colors">
              PHOW
            </Link>
            <nav className="hidden md:flex items-center gap-6">
              <Link href="/features" className="text-white/70 hover:text-white transition-colors text-sm font-medium">
                Features
              </Link>
              <Link href="/about" className="text-white/70 hover:text-white transition-colors text-sm font-medium">
                About
              </Link>
            </nav>
          </div>

          <div className="hidden md:flex items-center gap-3">
            {!authLoading && (
              <>
                {user ? (
                  <>
                    <Link
                      href="/dashboard"
                      className="px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white text-sm font-medium transition-all border border-white/20"
                    >
                      Dashboard
                    </Link>
                    <Link
                      href="/profile"
                      className="px-4 py-2 rounded-lg bg-gradient-to-r from-sky-500 to-blue-600 text-white text-sm font-medium hover:from-sky-400 hover:to-blue-500 transition-all shadow-lg shadow-sky-500/25"
                    >
                      {user.user_metadata?.full_name || user.email?.split("@")[0]}
                    </Link>
                  </>
                ) : (
                  <>
                    <button
                      onClick={signInWithGoogle}
                      disabled={!isConfigured}
                      className="px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white text-sm font-medium transition-all border border-white/20 disabled:opacity-50"
                    >
                      Sign In
                    </button>
                    <Link
                      href="/app"
                      className="px-4 py-2 rounded-lg bg-gradient-to-r from-sky-500 to-blue-600 text-white text-sm font-medium hover:from-sky-400 hover:to-blue-500 transition-all shadow-lg shadow-sky-500/25"
                    >
                      Get Started
                    </Link>
                  </>
                )}
              </>
            )}
          </div>
        </div>
      </header>

      {/* Main Layout with Sidebars */}
      <div className="relative z-10 flex-1 flex pt-16">
        {/* Left Sidebar - Chat History */}
        <aside
          className={`${
            leftSidebarOpen ? "w-64" : "w-0"
          } transition-all duration-300 overflow-hidden flex-shrink-0`}
        >
          <div className="h-full w-64 glass p-4 flex flex-col border-r border-white/10">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-white/80">Chat History</h2>
              <button
                onClick={handleNewChat}
                className="p-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-white transition-all"
                title="New Chat"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-1 custom-scrollbar">
              {user ? (
                conversations.length > 0 ? (
                  conversations.map((convo) => (
                    <button
                      key={convo.id}
                      className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-all ${
                        conversationId === convo.id
                          ? "bg-white/20 text-white"
                          : "text-white/60 hover:bg-white/10 hover:text-white"
                      }`}
                    >
                      <p className="truncate">{convo.title || "New conversation"}</p>
                      <p className="text-xs text-white/40 mt-0.5">
                        {new Date(convo.created_at).toLocaleDateString()}
                      </p>
                    </button>
                  ))
                ) : (
                  <p className="text-sm text-white/40 text-center py-4">No conversations yet</p>
                )
              ) : (
                <div className="text-center py-8">
                  <p className="text-sm text-white/40 mb-3">Sign in to save your chat history</p>
                  <button
                    onClick={signInWithGoogle}
                    disabled={!isConfigured}
                    className="px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-white text-xs font-medium transition-all border border-white/20 disabled:opacity-50"
                  >
                    Sign In
                  </button>
                </div>
              )}
            </div>
          </div>
        </aside>

        {/* Toggle Left Sidebar */}
        <button
          onClick={() => setLeftSidebarOpen(!leftSidebarOpen)}
          className="absolute left-0 top-1/2 -translate-y-1/2 z-20 p-1 bg-slate-800/80 hover:bg-slate-700 rounded-r-lg text-white/60 hover:text-white transition-all"
          style={{ left: leftSidebarOpen ? "256px" : "0" }}
        >
          <svg
            className={`w-4 h-4 transition-transform ${leftSidebarOpen ? "" : "rotate-180"}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        {/* Main Chat Area */}
        <main className="flex-1 flex flex-col min-w-0 pb-6">
          <div className="flex-1 max-w-3xl w-full mx-auto px-4 flex flex-col">
            {!hasMessages ? (
              /* Welcome State */
              <div className="flex-1 flex flex-col items-center justify-center py-8">
                <div className="text-center mb-10">
                  <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
                    What would you like to explore?
                  </h1>
                  <p className="text-lg text-white/60">
                    Ask anything about your business - locations, markets, competitors, and more.
                  </p>
                </div>

                {/* Tool Suggestion Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 w-full max-w-2xl mb-10">
                  {tools.map((tool) => {
                    const color = TOOL_COLORS[tool.id] || "from-gray-500 to-gray-600";
                    return (
                      <button
                        key={tool.id}
                        onClick={() => handleToolCardClick(tool)}
                        className="glass-card p-4 text-left hover:scale-[1.02] transition-all duration-200 group"
                      >
                        <div
                          className={`w-10 h-10 rounded-lg flex items-center justify-center text-xl mb-2 bg-gradient-to-br ${color} text-white shadow-md group-hover:scale-110 transition-transform`}
                        >
                          {tool.icon}
                        </div>
                        <p className="text-sm font-medium text-white truncate">{tool.name}</p>
                      </button>
                    );
                  })}
                </div>

                {/* Example Prompts */}
                <div className="w-full max-w-2xl space-y-2">
                  <p className="text-xs text-white/40 text-center mb-3">Try an example</p>
                  {EXAMPLE_PROMPTS.map((prompt, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleExampleClick(prompt)}
                      className="w-full text-left px-4 py-3 glass-card text-sm text-white/80 hover:text-white hover:bg-white/10 transition-all rounded-xl"
                    >
                      &ldquo;{prompt}&rdquo;
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              /* Chat Messages */
              <div className="flex-1 overflow-y-auto py-4 space-y-6 custom-scrollbar">
                {messages.map((msg) => (
                  <ChatMessage key={msg.id} role={msg.role} content={msg.content} />
                ))}

                {streamingContent && (
                  <ChatMessage role="assistant" content={streamingContent} isStreaming />
                )}

                <div ref={messagesEndRef} />
              </div>
            )}

            {/* Input Area */}
            <div className="mt-auto pt-4">
              <ChatInput
                onSend={handleSend}
                disabled={isLoading}
                placeholder="Ask anything about your business..."
                value={inputValue}
                onChange={setInputValue}
              />
            </div>
          </div>
        </main>

        {/* Toggle Right Sidebar */}
        <button
          onClick={() => setRightSidebarOpen(!rightSidebarOpen)}
          className="absolute right-0 top-1/2 -translate-y-1/2 z-20 p-1 bg-slate-800/80 hover:bg-slate-700 rounded-l-lg text-white/60 hover:text-white transition-all"
          style={{ right: rightSidebarOpen ? "256px" : "0" }}
        >
          <svg
            className={`w-4 h-4 transition-transform ${rightSidebarOpen ? "" : "rotate-180"}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>

        {/* Right Sidebar - Tools */}
        <aside
          className={`${
            rightSidebarOpen ? "w-64" : "w-0"
          } transition-all duration-300 overflow-hidden flex-shrink-0`}
        >
          <div className="h-full w-64 glass p-4 flex flex-col border-l border-white/10">
            <h2 className="text-sm font-semibold text-white/80 mb-4">Tools</h2>

            <div className="space-y-2">
              <button
                onClick={handleCopyChat}
                disabled={!hasMessages}
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-white/70 hover:text-white hover:bg-white/10 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                  />
                </svg>
                Copy conversation
              </button>

              <button
                onClick={handleExportPDF}
                disabled={!hasMessages}
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-white/70 hover:text-white hover:bg-white/10 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
                Export as PDF
              </button>

              <button
                onClick={handleNewChat}
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-white/70 hover:text-white hover:bg-white/10 transition-all"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M12 4v16m8-8H4"
                  />
                </svg>
                New chat
              </button>
            </div>

            {hasMessages && (
              <>
                <hr className="border-white/10 my-4" />
                <div className="text-xs text-white/40">
                  <p className="mb-1">Messages: {messages.length}</p>
                  {conversationId && (
                    <p className="truncate">ID: {conversationId.slice(0, 8)}...</p>
                  )}
                </div>
              </>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}

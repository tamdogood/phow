"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import { ChatMessage } from "@/components/chat/ChatMessage";
import { ChatInput } from "@/components/chat/ChatInput";
import { sendChatMessage, fetchConversations, updateConversationTitle } from "@/lib/api";
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
  location_scout: "bg-blue-500/20 text-blue-400",
  market_validator: "bg-purple-500/20 text-purple-400",
  competitor_analyzer: "bg-orange-500/20 text-orange-400",
  social_media_coach: "bg-pink-500/20 text-pink-400",
  review_responder: "bg-emerald-500/20 text-emerald-400",
  business_advisor: "bg-amber-500/20 text-amber-400",
};

const EXAMPLE_PROMPTS = [
  "Find the best location for my coffee shop in San Francisco",
  "Is there demand for a yoga studio in Austin?",
  "Who are my competitors for a bakery in downtown Seattle?",
  "Help me create social media content for my restaurant",
];

function detectTool(message: string): string {
  const lower = message.toLowerCase();

  // Check for "lost/unsure" phrases first - route to business_advisor
  if (
    lower.includes("don't know where to start") ||
    lower.includes("help me get started") ||
    lower.includes("what should i do") ||
    lower.includes("not sure where to begin") ||
    lower.includes("confused") ||
    lower.includes("overwhelmed") ||
    lower.includes("what can you help") ||
    lower.includes("what tools") ||
    lower.includes("recommend") ||
    lower.includes("figure out what i need")
  ) {
    return "business_advisor";
  }

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
  const { user, loading: authLoading } = useAuth();
  const [tools, setTools] = useState<Tool[]>([]);
  const [messages, setMessages] = useState<LocalMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [streamingContent, setStreamingContent] = useState("");
  const [inputValue, setInputValue] = useState("");
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [leftSidebarOpen, setLeftSidebarOpen] = useState(true);
  const [rightSidebarOpen, setRightSidebarOpen] = useState(false);
  const [editingConvoId, setEditingConvoId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");
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

  const loadConversations = useCallback(async () => {
    if (!user) return;
    const sessionId = getSessionId();
    if (!sessionId) return;
    try {
      const convos = await fetchConversations(sessionId, user.id);
      setConversations(convos);
    } catch (error) {
      console.error("Failed to fetch conversations:", error);
    }
  }, [user]);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

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
    await sendChatMessage(
      sessionId,
      toolId,
      message,
      conversationId,
      {
        onChunk: (content) => {
          fullResponse += content;
          setStreamingContent(fullResponse);
        },
        onDone: async (newConversationId) => {
          setConversationId(newConversationId);
          const assistantMessage: LocalMessage = {
            id: crypto.randomUUID(),
            role: "assistant",
            content: fullResponse,
          };
          setMessages((prev) => [...prev, assistantMessage]);
          setStreamingContent("");
          setIsLoading(false);
          await loadConversations();
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
      },
      user?.id
    );
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
    window.print();
  };

  const handleConversationClick = async (convo: Conversation) => {
    try {
      const { fetchMessages } = await import("@/lib/api");
      const msgs = await fetchMessages(convo.id);
      setConversationId(convo.id);
      setMessages(
        msgs.map((m) => ({
          id: m.id,
          role: m.role as "user" | "assistant",
          content: m.content,
        }))
      );
      setStreamingContent("");
    } catch (error) {
      console.error("Failed to load conversation:", error);
    }
  };

  const handleStartEditTitle = (convo: Conversation, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingConvoId(convo.id);
    setEditingTitle(convo.title || "");
  };

  const handleSaveTitle = async (convoId: string, e?: React.FormEvent) => {
    e?.preventDefault();
    if (!editingTitle.trim()) return;
    try {
      await updateConversationTitle(convoId, editingTitle.trim());
      setConversations((prev) =>
        prev.map((c) => (c.id === convoId ? { ...c, title: editingTitle.trim() } : c))
      );
      setEditingConvoId(null);
      setEditingTitle("");
    } catch (error) {
      console.error("Failed to update title:", error);
    }
  };

  const handleCancelEdit = () => {
    setEditingConvoId(null);
    setEditingTitle("");
  };

  const hasMessages = messages.length > 0 || streamingContent;

  return (
    <div className="h-screen bg-[#0a0a0a] relative flex flex-col">
      {/* Grid pattern overlay */}
      <div className="fixed inset-0 grid-pattern pointer-events-none" />

      {/* Header */}
      <header className="dark-header fixed top-0 left-0 right-0 z-50 px-6 py-4">
        <div className="mx-auto max-w-6xl flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/" className="text-xl font-bold text-white hover:text-white/80 transition-colors tracking-tight">
              PHOW
            </Link>
            <span className="hidden sm:inline-flex items-center px-2 py-0.5 rounded bg-white/10 text-[10px] font-mono text-white/60 uppercase tracking-wider">
              AI Analytics
            </span>
          </div>

          <div className="hidden md:flex items-center gap-3">
            {!authLoading && (
              <>
                {user ? (
                  <>
                    <Link
                      href="/dashboard"
                      className="px-4 py-2 text-white/70 hover:text-white text-sm font-medium transition-colors"
                    >
                      Dashboard
                    </Link>
                    <Link
                      href="/profile"
                      className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white text-black text-sm font-medium hover:bg-white/90 transition-all"
                    >
                      {user.user_metadata?.full_name || user.email?.split("@")[0]}
                    </Link>
                  </>
                ) : (
                  <>
                    <Link
                      href="/auth/signin"
                      className="px-4 py-2 text-white/70 hover:text-white text-sm font-medium transition-colors"
                    >
                      Sign In
                    </Link>
                    <Link
                      href="/"
                      className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white text-black text-sm font-medium hover:bg-white/90 transition-all"
                    >
                      Home
                    </Link>
                  </>
                )}
              </>
            )}
          </div>
        </div>
      </header>

      {/* Main Layout with Sidebars */}
      <div className="relative z-10 flex-1 flex pt-16 min-h-0">
        {/* Left Sidebar - Chat History */}
        <aside
          className={`${
            leftSidebarOpen ? "w-64" : "w-0"
          } transition-all duration-300 overflow-hidden flex-shrink-0 h-full`}
        >
          <div className="h-full w-64 bg-[#111] border-r border-white/5 p-4 flex flex-col">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-white/70">Chat History</h2>
              <button
                onClick={handleNewChat}
                className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-white/70 hover:text-white transition-all"
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
                    <div
                      key={convo.id}
                      className={`w-full rounded-lg text-sm transition-all ${
                        conversationId === convo.id
                          ? "bg-white/10"
                          : "hover:bg-white/5"
                      }`}
                    >
                      {editingConvoId === convo.id ? (
                        <form onSubmit={(e) => handleSaveTitle(convo.id, e)} className="p-2">
                          <input
                            type="text"
                            value={editingTitle}
                            onChange={(e) => setEditingTitle(e.target.value)}
                            onBlur={() => handleSaveTitle(convo.id)}
                            onKeyDown={(e) => {
                              if (e.key === "Escape") handleCancelEdit();
                            }}
                            autoFocus
                            className="w-full bg-white/10 border border-white/20 rounded px-2 py-1 text-white text-sm focus:outline-none focus:border-blue-500"
                          />
                        </form>
                      ) : (
                        <div
                          onClick={() => handleConversationClick(convo)}
                          className="flex items-start gap-2 px-3 py-2 cursor-pointer group"
                        >
                          <div className="flex-1 min-w-0">
                            <p className={`truncate ${conversationId === convo.id ? "text-white" : "text-white/50 group-hover:text-white/70"}`}>
                              {convo.title || "New conversation"}
                            </p>
                            <p className="text-xs text-white/30 mt-0.5">
                              {new Date(convo.created_at).toLocaleDateString()}
                            </p>
                          </div>
                          <button
                            onClick={(e) => handleStartEditTitle(convo, e)}
                            className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-white/10 transition-all flex-shrink-0"
                            title="Edit title"
                          >
                            <svg className="w-3 h-3 text-white/50 hover:text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                            </svg>
                          </button>
                        </div>
                      )}
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-white/30 text-center py-4">No conversations yet</p>
                )
              ) : (
                <div className="text-center py-8">
                  <p className="text-sm text-white/30 mb-3">Sign in to save history</p>
                  <Link
                    href="/auth/signin"
                    className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-white/70 text-xs font-medium transition-all border border-white/10"
                  >
                    Sign In
                  </Link>
                </div>
              )}
            </div>
          </div>
        </aside>

        {/* Toggle Left Sidebar */}
        <button
          onClick={() => setLeftSidebarOpen(!leftSidebarOpen)}
          className="absolute left-0 top-1/2 -translate-y-1/2 z-20 p-1 bg-[#1a1a1a] hover:bg-[#222] rounded-r-lg text-white/40 hover:text-white/70 transition-all border-y border-r border-white/5"
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
        <main className="flex-1 flex flex-col min-w-0 min-h-0">
          <div className="flex-1 max-w-3xl w-full mx-auto px-4 py-6 flex flex-col min-h-0">
            {!hasMessages ? (
              /* Welcome State */
              <div className="flex-1 overflow-y-auto flex flex-col items-center justify-center py-8 custom-scrollbar">
                <div className="text-center mb-10 animate-fade-in-up">
                  <h1 className="text-4xl md:text-5xl font-bold text-white mb-4 tracking-tight">
                    What would you like to <span className="text-accent-blue">explore</span>?
                  </h1>
                  <p className="text-lg text-white/50">
                    Ask anything about your business - locations, markets, competitors, and more.
                  </p>
                </div>

                {/* Help Me Get Started Card */}
                <button
                  onClick={() => setInputValue("I don't know where to start")}
                  className="w-full max-w-2xl mb-6 p-4 dark-card hover-lift animate-fade-in-up border border-amber-500/30 bg-amber-500/5"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-lg flex items-center justify-center text-2xl bg-amber-500/20 text-amber-400">
                      🧭
                    </div>
                    <div className="text-left">
                      <p className="text-base font-medium text-white">Not sure where to start?</p>
                      <p className="text-sm text-white/50">Tell us about your business and we&apos;ll guide you to the right tools</p>
                    </div>
                    <svg className="w-5 h-5 text-white/30 ml-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </button>

                {/* Tool Suggestion Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 w-full max-w-2xl mb-10">
                  {tools.map((tool, index) => {
                    const colorClass = TOOL_COLORS[tool.id] || "bg-gray-500/20 text-gray-400";
                    return (
                      <button
                        key={tool.id}
                        onClick={() => handleToolCardClick(tool)}
                        className="dark-card p-4 text-left hover-lift group animate-fade-in-up"
                        style={{ animationDelay: `${index * 0.1}s` }}
                      >
                        <div
                          className={`w-10 h-10 rounded-lg flex items-center justify-center text-xl mb-2 ${colorClass} group-hover:scale-110 transition-transform`}
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
                  <p className="text-xs text-white/30 text-center mb-3 font-mono uppercase tracking-wider">Try an example</p>
                  {EXAMPLE_PROMPTS.map((prompt, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleExampleClick(prompt)}
                      className="w-full text-left px-4 py-3 dark-card text-sm text-white/60 hover:text-white hover:bg-white/5 transition-all rounded-xl animate-fade-in-up"
                      style={{ animationDelay: `${(idx + 4) * 0.1}s` }}
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
          className="absolute right-0 top-1/2 -translate-y-1/2 z-20 p-1 bg-[#1a1a1a] hover:bg-[#222] rounded-l-lg text-white/40 hover:text-white/70 transition-all border-y border-l border-white/5"
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
          <div className="h-full w-64 bg-[#111] border-l border-white/5 p-4 flex flex-col">
            <h2 className="text-sm font-semibold text-white/70 mb-4">Tools</h2>

            <div className="space-y-2">
              <button
                onClick={handleCopyChat}
                disabled={!hasMessages}
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-white/50 hover:text-white hover:bg-white/5 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
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
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-white/50 hover:text-white hover:bg-white/5 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
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
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-white/50 hover:text-white hover:bg-white/5 transition-all"
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
                <hr className="border-white/5 my-4" />
                <div className="text-xs text-white/30 font-mono">
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

"use client";

import { useState, KeyboardEvent, useRef, useEffect } from "react";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
}

export function ChatInput({
  onSend,
  disabled = false,
  placeholder = "Ask PHOW to analyze your business...",
  value: controlledValue,
  onChange: controlledOnChange,
}: ChatInputProps) {
  const [internalMessage, setInternalMessage] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Support both controlled and uncontrolled modes
  const isControlled = controlledValue !== undefined && controlledOnChange !== undefined;
  const message = isControlled ? controlledValue : internalMessage;
  const setMessage = isControlled ? controlledOnChange : setInternalMessage;

  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSend(message.trim());
      setMessage("");
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
    }
  }, [message]);

  return (
    <div className="glass-input p-4 transition-all duration-200">
      {/* Textarea */}
      <textarea
        ref={textareaRef}
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        rows={1}
        className="w-full bg-transparent text-white placeholder:text-slate-500 resize-none outline-none text-sm leading-relaxed"
        style={{ minHeight: "24px", maxHeight: "120px" }}
      />

      {/* Bottom bar with actions */}
      <div className="flex items-center justify-between mt-3 pt-3 border-t border-slate-700/50">
        {/* Left side - optional action buttons */}
        <div className="flex items-center gap-2">
          {/* Placeholder for future features like attach, etc */}
          <span className="text-xs text-slate-500">Press Enter to send</span>
        </div>

        {/* Right side - send button */}
        <button
          onClick={handleSend}
          disabled={disabled || !message.trim()}
          className={`
            flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-all duration-200
            ${disabled || !message.trim()
              ? "bg-slate-700/50 text-slate-500 cursor-not-allowed"
              : "bg-sky-500 hover:bg-sky-400 text-white shadow-lg shadow-sky-500/25 hover:shadow-sky-400/40"
            }
          `}
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
          Chat
        </button>
      </div>
    </div>
  );
}

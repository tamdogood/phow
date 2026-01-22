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
  placeholder = "Ask anything about your business...",
  value: controlledValue,
  onChange: controlledOnChange,
}: ChatInputProps) {
  const [internalMessage, setInternalMessage] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const isControlled = controlledValue !== undefined && controlledOnChange !== undefined;
  const message = isControlled ? controlledValue : internalMessage;
  const setMessage = isControlled ? controlledOnChange : setInternalMessage;

  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSend(message.trim());
      setMessage("");
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

  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }
  }, [message]);

  return (
    <div className="relative glass-card p-3 pr-14">
      <textarea
        ref={textareaRef}
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        rows={1}
        className="w-full bg-transparent text-white placeholder:text-slate-400 resize-none outline-none text-base leading-relaxed"
        style={{ minHeight: "28px", maxHeight: "200px" }}
      />
      <button
        onClick={handleSend}
        disabled={disabled || !message.trim()}
        className={`
          absolute right-3 bottom-3 p-2 rounded-lg transition-all duration-200
          ${disabled || !message.trim()
            ? "bg-slate-700/50 text-slate-500 cursor-not-allowed"
            : "bg-white text-slate-900 hover:bg-white/90 shadow-lg"
          }
        `}
        aria-label="Send message"
      >
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
        </svg>
      </button>
    </div>
  );
}

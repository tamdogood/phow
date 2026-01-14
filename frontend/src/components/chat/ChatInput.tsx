"use client";

import { useState, KeyboardEvent } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

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
  placeholder = "Type your message...",
  value: controlledValue,
  onChange: controlledOnChange,
}: ChatInputProps) {
  const [internalMessage, setInternalMessage] = useState("");

  // Support both controlled and uncontrolled modes
  const isControlled = controlledValue !== undefined && controlledOnChange !== undefined;
  const message = isControlled ? controlledValue : internalMessage;
  const setMessage = isControlled ? controlledOnChange : setInternalMessage;

  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSend(message.trim());
      setMessage("");
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex gap-2">
      <Input
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        className="flex-1"
      />
      <Button onClick={handleSend} disabled={disabled || !message.trim()}>
        Send
      </Button>
    </div>
  );
}

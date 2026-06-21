"use client";

import { ElementType, ReactNode } from "react";
import { useIntersectionObserver } from "@/hooks/useIntersectionObserver";

interface RevealProps {
  children: ReactNode;
  /** ms delay before the reveal transition starts */
  delay?: number;
  className?: string;
  as?: ElementType;
}

/**
 * Scroll-triggered fade/translate reveal using the shared
 * `.dt-reveal` / `.dt-in` classes. Respects prefers-reduced-motion
 * (handled in CSS). One-shot by default.
 */
export function Reveal({ children, delay = 0, className = "", as: Tag = "div" }: RevealProps) {
  const { ref, isVisible } = useIntersectionObserver<HTMLElement>({
    threshold: 0.15,
    rootMargin: "0px 0px -8% 0px",
  });

  return (
    <Tag
      ref={ref}
      className={`dt-reveal ${isVisible ? "dt-in" : ""} ${className}`}
      style={{ transitionDelay: `${delay}ms` }}
    >
      {children}
    </Tag>
  );
}

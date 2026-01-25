import React from 'react';
import { Sparkles, AlertCircle, CheckCircle } from 'lucide-react';

interface AIInsightCalloutProps {
  insight: string;
  type?: 'positive' | 'neutral' | 'warning';
}

export const AIInsightCallout: React.FC<AIInsightCalloutProps> = ({
  insight,
  type = 'neutral',
}) => {
  const config = {
    positive: {
      icon: CheckCircle,
      bgClass: 'bg-gradient-to-r from-green-500/20 to-emerald-500/20',
      borderClass: 'border-green-500/30',
      iconClass: 'text-green-400',
      glowClass: 'shadow-[0_0_20px_rgba(34,197,94,0.3)]',
    },
    neutral: {
      icon: Sparkles,
      bgClass: 'bg-gradient-to-r from-blue-500/20 via-purple-500/20 to-pink-500/20',
      borderClass: 'border-purple-500/30',
      iconClass: 'text-purple-400',
      glowClass: 'shadow-[0_0_20px_rgba(139,92,246,0.3)]',
    },
    warning: {
      icon: AlertCircle,
      bgClass: 'bg-gradient-to-r from-orange-500/20 to-yellow-500/20',
      borderClass: 'border-orange-500/30',
      iconClass: 'text-orange-400',
      glowClass: 'shadow-[0_0_20px_rgba(249,115,22,0.3)]',
    },
  };

  const { icon: Icon, bgClass, borderClass, iconClass, glowClass } = config[type];

  return (
    <div
      className={`
        ai-insight-pill
        ${bgClass}
        ${glowClass}
        rounded-full px-4 py-3
        border ${borderClass}
        flex items-center gap-3
        backdrop-blur-sm
        transition-all duration-300 hover:scale-[1.02]
      `}
    >
      <Icon className={`w-5 h-5 ${iconClass} flex-shrink-0 animate-pulse`} />
      <p className="text-sm text-slate-100 font-medium leading-relaxed">
        {insight}
      </p>
    </div>
  );
};

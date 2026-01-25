import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface ScoreCardProps {
  score: number;
  maxScore?: number;
  label: string;
  trend?: 'up' | 'down';
  trendValue?: string;
  color?: 'green' | 'blue' | 'yellow' | 'red';
  grade?: string;
}

export const ScoreCard: React.FC<ScoreCardProps> = ({
  score,
  maxScore = 100,
  label,
  trend,
  trendValue,
  color,
  grade,
}) => {
  const percentage = (score / maxScore) * 100;

  const getColor = (): string => {
    if (color) return color;
    if (percentage >= 80) return 'green';
    if (percentage >= 60) return 'yellow';
    if (percentage >= 40) return 'orange';
    return 'red';
  };

  const scoreColor = getColor();
  const gradientClass = `progress-bar-gradient-${scoreColor === 'orange' ? 'yellow' : scoreColor}`;

  return (
    <div className="widget-card p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="text-sm text-slate-400">{label}</div>
        {trend && trendValue && (
          <div className={`flex items-center gap-1 text-xs px-2 py-1 rounded-full ${
            trend === 'up' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
          }`}>
            {trend === 'up' ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
            {trendValue}
          </div>
        )}
      </div>

      <div className="flex items-baseline gap-2 mb-3">
        <div className="text-4xl font-bold text-white">
          {grade || score}
        </div>
        {!grade && <div className="text-lg text-slate-400">/ {maxScore}</div>}
      </div>

      <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
        <div
          className={`h-full ${gradientClass} transition-all duration-500`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

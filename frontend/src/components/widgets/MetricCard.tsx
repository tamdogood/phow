import React from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  icon: LucideIcon;
  label: string;
  value: string | number;
  subtext?: string;
  iconColor?: string;
  iconBgColor?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  icon: Icon,
  label,
  value,
  subtext,
  iconColor = 'text-blue-400',
  iconBgColor = 'bg-blue-500/20',
}) => {
  return (
    <div className="widget-card p-4">
      <div className="flex items-start gap-3">
        <div className={`metric-icon-badge ${iconBgColor}`}>
          <Icon className={`w-5 h-5 ${iconColor}`} />
        </div>
        <div className="flex-1">
          <div className="text-sm text-slate-400 mb-1">{label}</div>
          <div className="text-2xl font-bold text-white">{value}</div>
          {subtext && <div className="text-xs text-slate-500 mt-1">{subtext}</div>}
        </div>
      </div>
    </div>
  );
};

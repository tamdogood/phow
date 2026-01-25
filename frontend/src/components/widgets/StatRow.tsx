import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatRowProps {
  icon: LucideIcon;
  label: string;
  value: string | number;
  color?: string;
}

export const StatRow: React.FC<StatRowProps> = ({
  icon: Icon,
  label,
  value,
  color = 'text-slate-400',
}) => {
  return (
    <div className="flex items-center justify-between py-2">
      <div className="flex items-center gap-2">
        <Icon className={`w-4 h-4 ${color}`} />
        <span className="text-sm text-slate-300">{label}</span>
      </div>
      <span className="text-sm font-medium text-white">{value}</span>
    </div>
  );
};

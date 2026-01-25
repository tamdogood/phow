import React from 'react';
import { DollarSign } from 'lucide-react';

interface PriceLevelProps {
  level: number;
  maxLevel?: number;
  size?: 'sm' | 'md' | 'lg';
}

export const PriceLevel: React.FC<PriceLevelProps> = ({
  level,
  maxLevel = 4,
  size = 'md',
}) => {
  const sizeClasses = {
    sm: 'w-3 h-3',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
  };

  return (
    <div className="flex items-center gap-0.5">
      {Array.from({ length: maxLevel }).map((_, index) => (
        <DollarSign
          key={index}
          className={`${sizeClasses[size]} ${
            index < level ? 'text-green-400 fill-green-400' : 'text-slate-600'
          }`}
        />
      ))}
    </div>
  );
};

import React from 'react';
import { Star } from 'lucide-react';

interface RatingDisplayProps {
  rating: number;
  reviewCount?: number;
  size?: 'sm' | 'md' | 'lg';
  showNumeric?: boolean;
}

export const RatingDisplay: React.FC<RatingDisplayProps> = ({
  rating,
  reviewCount,
  size = 'md',
  showNumeric = true,
}) => {
  const sizeClasses = {
    sm: 'w-3 h-3',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
  };

  const textSizeClasses = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  };

  const renderStars = () => {
    return Array.from({ length: 5 }).map((_, index) => {
      const fillPercentage = Math.min(Math.max(rating - index, 0), 1);

      return (
        <div key={index} className="relative">
          <Star className={`${sizeClasses[size]} text-slate-600`} />
          {fillPercentage > 0 && (
            <div
              className="absolute inset-0 overflow-hidden"
              style={{ width: `${fillPercentage * 100}%` }}
            >
              <Star className={`${sizeClasses[size]} text-yellow-400 fill-yellow-400`} />
            </div>
          )}
        </div>
      );
    });
  };

  return (
    <div className="flex items-center gap-2">
      <div className="flex items-center gap-0.5">
        {renderStars()}
      </div>
      {showNumeric && (
        <span className={`${textSizeClasses[size]} font-medium text-slate-300`}>
          {rating.toFixed(1)}
        </span>
      )}
      {reviewCount && (
        <span className={`${textSizeClasses[size]} text-slate-500`}>
          ({reviewCount.toLocaleString()})
        </span>
      )}
    </div>
  );
};

import React from 'react';
import { Store, Train, Users } from 'lucide-react';
import { RatingDisplay } from './RatingDisplay';
import { PriceLevel } from './PriceLevel';
import { StatRow } from './StatRow';

interface LocationData {
  competitors?: Array<{
    name: string;
    rating?: number;
    price_level?: number;
  }>;
  transit_stations?: Array<{ name: string }>;
  analysis_summary?: {
    competitor_count?: number;
    transit_access?: boolean;
    foot_traffic_indicators?: number;
  };
}

interface LocationInfoCardsProps {
  data: LocationData;
}

export const LocationInfoCards: React.FC<LocationInfoCardsProps> = ({ data }) => {
  const { competitors = [], transit_stations = [], analysis_summary } = data;

  // Calculate competitor metrics
  const competitorCount = analysis_summary?.competitor_count || competitors.length;
  const competitorsWithRating = competitors.filter(c => c.rating);
  const avgRating = competitorsWithRating.length > 0
    ? competitorsWithRating.reduce((sum, c) => sum + (c.rating || 0), 0) / competitorsWithRating.length
    : 0;

  const competitorsWithPrice = competitors.filter(c => c.price_level);
  const avgPriceLevel = competitorsWithPrice.length > 0
    ? Math.round(competitorsWithPrice.reduce((sum, c) => sum + (c.price_level || 0), 0) / competitorsWithPrice.length)
    : 0;

  // Calculate transit metrics
  const transitStationCount = transit_stations.length;
  const hasTransit = analysis_summary?.transit_access || transitStationCount > 0;
  const transitGrade = transitStationCount >= 5 ? 'A+' :
                       transitStationCount >= 3 ? 'A' :
                       transitStationCount === 2 ? 'B' :
                       transitStationCount === 1 ? 'C' : 'D';

  // Calculate foot traffic level
  const footTrafficIndicators = analysis_summary?.foot_traffic_indicators || 0;
  const footTrafficLevel = footTrafficIndicators >= 40 ? 'High' :
                           footTrafficIndicators >= 20 ? 'Medium' : 'Low';

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 my-4">
      {/* Competitors Card */}
      <div className="widget-card p-4">
        <div className="flex items-center gap-3 mb-4">
          <div className="metric-icon-badge bg-orange-500/20">
            <Store className="w-5 h-5 text-orange-400" />
          </div>
          <h3 className="text-base font-semibold text-white">Competitors</h3>
        </div>
        <div className="space-y-3">
          <div>
            <div className="text-sm text-slate-400 mb-1">Within 0.5 mi</div>
            <div className="text-2xl font-bold text-white">{competitorCount}</div>
          </div>
          {avgRating > 0 && (
            <div>
              <div className="text-sm text-slate-400 mb-1">Avg Rating</div>
              <RatingDisplay rating={avgRating} size="sm" />
            </div>
          )}
          {avgPriceLevel > 0 && (
            <div>
              <div className="text-sm text-slate-400 mb-1">Price Level</div>
              <PriceLevel level={avgPriceLevel} size="sm" />
            </div>
          )}
        </div>
      </div>

      {/* Transit Access Card */}
      <div className="widget-card p-4">
        <div className="flex items-center gap-3 mb-4">
          <div className="metric-icon-badge bg-blue-500/20">
            <Train className="w-5 h-5 text-blue-400" />
          </div>
          <h3 className="text-base font-semibold text-white">Transit Access</h3>
        </div>
        <div className="space-y-3">
          <div>
            <div className="text-sm text-slate-400 mb-1">Grade</div>
            <div className="text-2xl font-bold text-white">{transitGrade}</div>
          </div>
          <div>
            <div className="text-sm text-slate-400 mb-1">Stations Nearby</div>
            <div className="text-xl font-semibold text-white">{transitStationCount}</div>
          </div>
          <div>
            <div className="text-sm text-slate-400 mb-1">Access</div>
            <div className={`text-sm font-medium ${hasTransit ? 'text-green-400' : 'text-red-400'}`}>
              {hasTransit ? 'Available' : 'Limited'}
            </div>
          </div>
        </div>
      </div>

      {/* Demographics Card */}
      <div className="widget-card p-4">
        <div className="flex items-center gap-3 mb-4">
          <div className="metric-icon-badge bg-purple-500/20">
            <Users className="w-5 h-5 text-purple-400" />
          </div>
          <h3 className="text-base font-semibold text-white">Demographics</h3>
        </div>
        <div className="space-y-3">
          <div>
            <div className="text-sm text-slate-400 mb-1">Foot Traffic</div>
            <div className={`text-xl font-semibold ${
              footTrafficLevel === 'High' ? 'text-green-400' :
              footTrafficLevel === 'Medium' ? 'text-yellow-400' : 'text-orange-400'
            }`}>
              {footTrafficLevel}
            </div>
          </div>
          <div>
            <div className="text-sm text-slate-400 mb-1">Indicators</div>
            <div className="text-xl font-semibold text-white">{footTrafficIndicators}</div>
          </div>
        </div>
      </div>
    </div>
  );
};

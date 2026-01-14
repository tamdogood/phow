"use client";

import { useState } from "react";

interface SocialContentData {
  type: "social_content";
  location?: {
    lat: number;
    lng: number;
    city?: string;
    state?: string;
    country?: string;
    timezone?: string;
  };
  weather?: {
    temperature?: number;
    feels_like?: number;
    humidity?: number;
    description?: string;
    icon?: string;
    impact?: {
      sentiment?: string;
      opportunities?: string[];
      content_suggestions?: string[];
    };
  };
  events?: {
    holidays?: Array<{
      name: string;
      date: string;
      type: string;
    }>;
    daily_themes?: Array<{
      name: string;
      hashtag: string;
      description?: string;
    }>;
    local_events?: Array<{
      name: string;
      date?: string;
      venue?: string;
      type?: string;
    }>;
  };
  hashtags?: {
    trending?: string[];
    industry?: string[];
    local?: string[];
    seasonal?: string[];
  };
  posting_times?: {
    platform?: string;
    best_times?: Array<{
      day: string;
      times: string[];
    }>;
    timezone?: string;
  };
}

interface SocialMediaCoachWidgetProps {
  data: SocialContentData;
}

function WeatherCard({ weather }: { weather: SocialContentData["weather"] }) {
  if (!weather) return null;

  const getWeatherEmoji = (desc?: string) => {
    if (!desc) return "🌤️";
    const d = desc.toLowerCase();
    if (d.includes("clear") || d.includes("sunny")) return "☀️";
    if (d.includes("cloud")) return "☁️";
    if (d.includes("rain")) return "🌧️";
    if (d.includes("snow")) return "❄️";
    if (d.includes("thunder")) return "⛈️";
    if (d.includes("fog") || d.includes("mist")) return "🌫️";
    return "🌤️";
  };

  return (
    <div className="bg-gradient-to-r from-sky-500/20 to-blue-500/20 rounded-lg p-3 border border-sky-500/30">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{getWeatherEmoji(weather.description)}</span>
          <div>
            <div className="text-lg font-semibold text-slate-100">
              {weather.temperature ? `${Math.round(weather.temperature)}°F` : "--"}
            </div>
            <div className="text-xs text-slate-400 capitalize">{weather.description || "No data"}</div>
          </div>
        </div>
        {weather.impact?.sentiment && (
          <div className={`px-2 py-1 rounded-full text-xs font-medium ${
            weather.impact.sentiment === "positive"
              ? "bg-green-500/20 text-green-400"
              : weather.impact.sentiment === "negative"
              ? "bg-red-500/20 text-red-400"
              : "bg-slate-500/20 text-slate-400"
          }`}>
            {weather.impact.sentiment === "positive" ? "Great for business!" :
             weather.impact.sentiment === "negative" ? "Plan accordingly" : "Neutral"}
          </div>
        )}
      </div>
      {weather.impact?.opportunities && weather.impact.opportunities.length > 0 && (
        <div className="mt-2 pt-2 border-t border-sky-500/20">
          <div className="text-xs text-slate-400 mb-1">Content opportunities:</div>
          <div className="flex flex-wrap gap-1">
            {weather.impact.opportunities.slice(0, 3).map((opp, idx) => (
              <span key={idx} className="text-xs bg-sky-500/20 text-sky-300 px-2 py-0.5 rounded">
                {opp}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function HashtagSection({ hashtags }: { hashtags: SocialContentData["hashtags"] }) {
  if (!hashtags) return null;

  const [copiedTag, setCopiedTag] = useState<string | null>(null);

  const handleCopy = (tag: string) => {
    navigator.clipboard.writeText(tag);
    setCopiedTag(tag);
    setTimeout(() => setCopiedTag(null), 2000);
  };

  const allTags = [
    ...(hashtags.trending || []),
    ...(hashtags.industry || []),
    ...(hashtags.local || []),
    ...(hashtags.seasonal || []),
  ].slice(0, 12);

  if (allTags.length === 0) return null;

  return (
    <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-sm">#️⃣</span>
        <span className="text-sm font-medium text-slate-200">Suggested Hashtags</span>
      </div>
      <div className="flex flex-wrap gap-1.5">
        {allTags.map((tag, idx) => (
          <button
            key={idx}
            onClick={() => handleCopy(tag)}
            className="text-xs bg-slate-700/50 text-sky-400 px-2 py-1 rounded-full hover:bg-sky-500/20 transition-colors cursor-pointer"
            title="Click to copy"
          >
            {copiedTag === tag ? "✓ Copied!" : tag}
          </button>
        ))}
      </div>
    </div>
  );
}

function EventsSection({ events }: { events: SocialContentData["events"] }) {
  if (!events) return null;

  const hasContent = (events.holidays && events.holidays.length > 0) ||
                     (events.daily_themes && events.daily_themes.length > 0) ||
                     (events.local_events && events.local_events.length > 0);

  if (!hasContent) return null;

  return (
    <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-sm">📅</span>
        <span className="text-sm font-medium text-slate-200">Upcoming Events & Themes</span>
      </div>
      <div className="space-y-2">
        {events.holidays && events.holidays.length > 0 && (
          <div>
            <div className="text-xs text-slate-400 mb-1">Holidays</div>
            <div className="flex flex-wrap gap-1.5">
              {events.holidays.slice(0, 3).map((holiday, idx) => (
                <span key={idx} className="text-xs bg-purple-500/20 text-purple-300 px-2 py-1 rounded-full">
                  🎉 {holiday.name}
                </span>
              ))}
            </div>
          </div>
        )}
        {events.daily_themes && events.daily_themes.length > 0 && (
          <div>
            <div className="text-xs text-slate-400 mb-1">Today&apos;s Themes</div>
            <div className="flex flex-wrap gap-1.5">
              {events.daily_themes.slice(0, 4).map((theme, idx) => (
                <span key={idx} className="text-xs bg-amber-500/20 text-amber-300 px-2 py-1 rounded-full">
                  {theme.hashtag}
                </span>
              ))}
            </div>
          </div>
        )}
        {events.local_events && events.local_events.length > 0 && (
          <div>
            <div className="text-xs text-slate-400 mb-1">Local Events</div>
            <div className="space-y-1">
              {events.local_events.slice(0, 3).map((event, idx) => (
                <div key={idx} className="text-xs text-slate-300 flex items-center gap-2">
                  <span className="text-sky-400">→</span>
                  <span>{event.name}</span>
                  {event.venue && <span className="text-slate-500">@ {event.venue}</span>}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function PostingTimesSection({ postingTimes }: { postingTimes: SocialContentData["posting_times"] }) {
  if (!postingTimes || !postingTimes.best_times || postingTimes.best_times.length === 0) return null;

  return (
    <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-sm">⏰</span>
        <span className="text-sm font-medium text-slate-200">
          Best Posting Times
          {postingTimes.platform && <span className="text-slate-400 font-normal"> for {postingTimes.platform}</span>}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-2">
        {postingTimes.best_times.slice(0, 4).map((dayTime, idx) => (
          <div key={idx} className="bg-slate-900/50 rounded px-2 py-1.5">
            <div className="text-xs font-medium text-slate-300">{dayTime.day}</div>
            <div className="text-xs text-sky-400">{dayTime.times.join(", ")}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function SocialMediaCoachWidget({ data }: SocialMediaCoachWidgetProps) {
  const locationStr = data.location
    ? [data.location.city, data.location.state].filter(Boolean).join(", ")
    : "your area";

  return (
    <div className="w-full bg-slate-900 rounded-xl shadow-lg border border-slate-700 overflow-hidden my-3">
      {/* Header */}
      <div className="bg-gradient-to-r from-sky-600 to-blue-600 px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="text-xl">📱</span>
          <div>
            <h3 className="text-white font-semibold">Social Media Coach</h3>
            <p className="text-sky-100 text-sm">Content insights for {locationStr}</p>
          </div>
        </div>
      </div>

      {/* Content sections */}
      <div className="p-4 space-y-3">
        {/* Weather */}
        <WeatherCard weather={data.weather} />

        {/* Events & Themes */}
        <EventsSection events={data.events} />

        {/* Hashtags */}
        <HashtagSection hashtags={data.hashtags} />

        {/* Posting Times */}
        <PostingTimesSection postingTimes={data.posting_times} />
      </div>

      {/* Footer tip */}
      <div className="px-4 py-2 bg-slate-800/50 border-t border-slate-700">
        <p className="text-xs text-slate-400">
          💡 Tip: Use these insights to create timely, engaging content that resonates with your local audience.
        </p>
      </div>
    </div>
  );
}

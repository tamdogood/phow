"use client";

import { useState } from "react";

interface SentimentAnalysis {
  sentiment: string;
  rating?: number;
  key_issues: string[];
  emotional_tone: string;
  review_type: string;
  positive_mentions?: number;
  negative_mentions?: number;
}

interface ResponseData {
  tone: string;
  sentiment: string;
  key_issues: string[];
  guidelines: {
    opening: string;
    style: string;
    focus: string;
  };
  business_name: string;
}

interface ReviewResponseData {
  type: "review_response";
  original_review: string;
  sentiment_analysis: SentimentAnalysis | null;
  responses: ResponseData[];
}

interface ReviewResponderWidgetProps {
  data: ReviewResponseData;
}

function SentimentBadge({ sentiment }: { sentiment: string }) {
  const config: Record<string, { emoji: string; bg: string; text: string }> = {
    positive: { emoji: "😊", bg: "bg-green-500/20", text: "text-green-400" },
    negative: { emoji: "😞", bg: "bg-red-500/20", text: "text-red-400" },
    mixed: { emoji: "😐", bg: "bg-amber-500/20", text: "text-amber-400" },
    neutral: { emoji: "😶", bg: "bg-slate-500/20", text: "text-slate-400" },
  };

  const { emoji, bg, text } = config[sentiment] || config.neutral;

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-sm font-medium ${bg} ${text}`}>
      <span>{emoji}</span>
      <span className="capitalize">{sentiment}</span>
    </span>
  );
}

function EmotionBadge({ emotion }: { emotion: string }) {
  const emotionConfig: Record<string, { emoji: string; color: string }> = {
    angry: { emoji: "😤", color: "text-red-400" },
    frustrated: { emoji: "😫", color: "text-orange-400" },
    disappointed: { emoji: "😔", color: "text-amber-400" },
    neutral: { emoji: "😐", color: "text-slate-400" },
    satisfied: { emoji: "😌", color: "text-green-400" },
    enthusiastic: { emoji: "🤩", color: "text-emerald-400" },
  };

  const { emoji, color } = emotionConfig[emotion] || emotionConfig.neutral;

  return (
    <span className={`inline-flex items-center gap-1 text-sm ${color}`}>
      <span>{emoji}</span>
      <span className="capitalize">{emotion}</span>
    </span>
  );
}

function IssueTag({ issue }: { issue: string }) {
  return (
    <span className="inline-block px-2 py-0.5 rounded-full text-xs bg-slate-700/50 text-slate-300 border border-slate-600">
      {issue}
    </span>
  );
}

function ReviewCard({ review }: { review: string }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const shouldTruncate = review.length > 200;
  const displayText = shouldTruncate && !isExpanded ? review.slice(0, 200) + "..." : review;

  return (
    <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-sm">💬</span>
        <span className="text-sm font-medium text-slate-200">Original Review</span>
      </div>
      <p className="text-sm text-slate-300 italic">&quot;{displayText}&quot;</p>
      {shouldTruncate && (
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-xs text-sky-400 mt-1 hover:text-sky-300"
        >
          {isExpanded ? "Show less" : "Show more"}
        </button>
      )}
    </div>
  );
}

function AnalysisCard({ analysis }: { analysis: SentimentAnalysis }) {
  return (
    <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-sm">🔍</span>
        <span className="text-sm font-medium text-slate-200">Analysis</span>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <div className="text-xs text-slate-400 mb-1">Sentiment</div>
          <SentimentBadge sentiment={analysis.sentiment} />
        </div>
        <div>
          <div className="text-xs text-slate-400 mb-1">Customer Emotion</div>
          <EmotionBadge emotion={analysis.emotional_tone} />
        </div>
      </div>

      {analysis.key_issues && analysis.key_issues.length > 0 && (
        <div className="mt-3">
          <div className="text-xs text-slate-400 mb-1.5">Key Issues</div>
          <div className="flex flex-wrap gap-1.5">
            {analysis.key_issues.map((issue, idx) => (
              <IssueTag key={idx} issue={issue} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function ToneCard({ tone, guidelines, isActive, onClick }: {
  tone: string;
  guidelines: { opening: string; style: string; focus: string };
  isActive: boolean;
  onClick: () => void;
}) {
  const toneConfig: Record<string, { emoji: string; color: string; gradient: string }> = {
    professional: {
      emoji: "👔",
      color: "text-blue-400",
      gradient: "from-blue-600/20 to-indigo-600/20"
    },
    friendly: {
      emoji: "😊",
      color: "text-green-400",
      gradient: "from-green-600/20 to-emerald-600/20"
    },
    apologetic: {
      emoji: "🙏",
      color: "text-amber-400",
      gradient: "from-amber-600/20 to-orange-600/20"
    },
  };

  const { emoji, color, gradient } = toneConfig[tone] || toneConfig.professional;

  return (
    <button
      onClick={onClick}
      className={`w-full text-left p-3 rounded-lg border transition-all ${
        isActive
          ? `bg-gradient-to-r ${gradient} border-sky-500/50`
          : "bg-slate-800/30 border-slate-700 hover:border-slate-600"
      }`}
    >
      <div className="flex items-center gap-2 mb-1">
        <span>{emoji}</span>
        <span className={`text-sm font-medium capitalize ${color}`}>{tone}</span>
        {isActive && <span className="text-xs text-sky-400 ml-auto">Selected</span>}
      </div>
      <p className="text-xs text-slate-400">{guidelines.style}</p>
    </button>
  );
}

export function ReviewResponderWidget({ data }: ReviewResponderWidgetProps) {
  const [selectedTone, setSelectedTone] = useState<string>("professional");
  const [copiedTone, setCopiedTone] = useState<string | null>(null);

  const handleCopy = (text: string, tone: string) => {
    navigator.clipboard.writeText(text);
    setCopiedTone(tone);
    setTimeout(() => setCopiedTone(null), 2000);
  };

  const selectedResponse = data.responses.find(r => r.tone === selectedTone);

  return (
    <div className="w-full bg-slate-900 rounded-xl shadow-lg border border-slate-700 overflow-hidden my-3">
      {/* Header */}
      <div className="bg-gradient-to-r from-amber-600 to-orange-600 px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="text-xl">⭐</span>
          <div>
            <h3 className="text-white font-semibold">Review Response Assistant</h3>
            <p className="text-amber-100 text-sm">AI-powered response drafts</p>
          </div>
        </div>
      </div>

      <div className="p-4 space-y-3">
        {/* Original Review */}
        <ReviewCard review={data.original_review} />

        {/* Sentiment Analysis */}
        {data.sentiment_analysis && (
          <AnalysisCard analysis={data.sentiment_analysis} />
        )}

        {/* Tone Selector */}
        {data.responses.length > 0 && (
          <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-sm">🎨</span>
              <span className="text-sm font-medium text-slate-200">Response Tone</span>
            </div>
            <div className="grid grid-cols-3 gap-2">
              {data.responses.map((response) => (
                <ToneCard
                  key={response.tone}
                  tone={response.tone}
                  guidelines={response.guidelines}
                  isActive={selectedTone === response.tone}
                  onClick={() => setSelectedTone(response.tone)}
                />
              ))}
            </div>
          </div>
        )}

        {/* Response Preview */}
        {selectedResponse && (
          <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="text-sm">📝</span>
                <span className="text-sm font-medium text-slate-200">Response Preview</span>
              </div>
              <button
                onClick={() => handleCopy(selectedResponse.guidelines.opening, selectedResponse.tone)}
                className="px-2 py-1 text-xs bg-sky-600/20 text-sky-400 rounded hover:bg-sky-600/30 transition-colors"
              >
                {copiedTone === selectedResponse.tone ? "✓ Copied!" : "📋 Copy"}
              </button>
            </div>
            <div className="bg-slate-900/50 rounded p-3 border border-slate-600">
              <p className="text-sm text-slate-300">{selectedResponse.guidelines.opening}</p>
              <p className="text-xs text-slate-500 mt-2 italic">
                Focus: {selectedResponse.guidelines.focus}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Footer tip */}
      <div className="px-4 py-2 bg-slate-800/50 border-t border-slate-700">
        <p className="text-xs text-slate-400">
          💡 Tip: Respond to reviews within 24-48 hours for best customer relations.
        </p>
      </div>
    </div>
  );
}

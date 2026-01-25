"use client";

import Link from "next/link";
import { CommunityPost } from "@/types";

function formatRelativeTime(date: string): string {
  const now = Date.now();
  const then = new Date(date).getTime();
  const seconds = Math.floor((now - then) / 1000);
  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
  return new Date(date).toLocaleDateString();
}

const categoryColors: Record<string, string> = {
  question: "bg-amber-500/20 text-amber-400",
  advice: "bg-emerald-500/20 text-emerald-400",
  update: "bg-blue-500/20 text-blue-400",
  discussion: "bg-purple-500/20 text-purple-400",
};

function PostRow({ post }: { post: CommunityPost }) {
  const authorName = post.business_profiles?.business_name || "Anonymous";

  return (
    <Link href={`/community/${post.id}`}>
      <div className="flex items-center justify-between py-3 border-b border-white/5 last:border-0 hover:bg-white/5 -mx-2 px-2 rounded transition-colors">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            {post.category && (
              <span className={`px-1.5 py-0.5 text-[10px] rounded capitalize ${categoryColors[post.category] || "bg-white/10 text-white/60"}`}>
                {post.category}
              </span>
            )}
            <h4 className="text-white font-medium text-sm truncate">{post.title}</h4>
          </div>
          <div className="flex items-center gap-2 text-xs text-white/40">
            <span>{authorName}</span>
            {post.comment_count > 0 && (
              <>
                <span className="text-white/20">|</span>
                <span>{post.comment_count} {post.comment_count === 1 ? "comment" : "comments"}</span>
              </>
            )}
            <span className="text-white/20">|</span>
            <span>{formatRelativeTime(post.created_at)}</span>
          </div>
        </div>
      </div>
    </Link>
  );
}

interface CommunityWidgetProps {
  posts: CommunityPost[];
  loading?: boolean;
}

export function CommunityWidget({ posts, loading }: CommunityWidgetProps) {
  if (loading) {
    return (
      <div className="dark-card p-6 mb-6 animate-pulse">
        <div className="flex items-center justify-between mb-4">
          <div className="h-6 w-24 bg-white/10 rounded" />
          <div className="h-4 w-16 bg-white/10 rounded" />
        </div>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-12 bg-white/5 rounded" />
          ))}
        </div>
      </div>
    );
  }

  if (posts.length === 0) {
    return (
      <div className="dark-card p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white">Community</h2>
          <Link href="/community" className="text-blue-400 text-sm hover:underline">
            View All
          </Link>
        </div>
        <div className="text-center py-4">
          <p className="text-white/40 text-sm mb-3">No posts yet. Be the first to share!</p>
          <Link
            href="/community"
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 text-white text-sm hover:bg-white/10 transition-all"
          >
            Create Post
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="dark-card p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white">Community</h2>
        <Link href="/community" className="text-blue-400 text-sm hover:underline">
          View All
        </Link>
      </div>
      <div>
        {posts.slice(0, 5).map((post) => (
          <PostRow key={post.id} post={post} />
        ))}
      </div>
    </div>
  );
}

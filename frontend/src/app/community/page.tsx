"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { getCommunityFeed, createPost } from "@/lib/api";
import { getSessionId } from "@/lib/session";
import { CommunityPost } from "@/types";

const CATEGORIES = [
  { id: null, label: "All" },
  { id: "question", label: "Questions" },
  { id: "advice", label: "Advice" },
  { id: "update", label: "Updates" },
  { id: "discussion", label: "Discussion" },
];

const SORT_OPTIONS = [
  { id: "newest", label: "Newest" },
  { id: "oldest", label: "Oldest" },
  { id: "most_comments", label: "Most Comments" },
];

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

function CategoryBadge({ category }: { category: string | null }) {
  if (!category) return null;
  const colors: Record<string, string> = {
    question: "bg-amber-500/20 text-amber-400 border-amber-500/30",
    advice: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
    update: "bg-sky-500/20 text-sky-400 border-sky-500/30",
    discussion: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  };
  return (
    <span className={`px-2 py-0.5 text-xs rounded-full border ${colors[category] || "bg-white/10 text-white/60"}`}>
      {category}
    </span>
  );
}

function PostCard({ post }: { post: CommunityPost }) {
  const authorName = post.business_profiles?.business_name || "Anonymous";

  return (
    <Link href={`/community/${post.id}`}>
      <div className="glass-card p-5 cursor-pointer">
        <div className="flex items-start justify-between gap-3 mb-2">
          <h3 className="text-white font-semibold text-lg line-clamp-1">{post.title}</h3>
          <CategoryBadge category={post.category} />
        </div>
        <p className="text-white/60 text-sm line-clamp-2 mb-3">{post.content}</p>
        <div className="flex items-center justify-between text-xs text-white/40">
          <div className="flex items-center gap-3">
            <span>{authorName}</span>
            <span className="text-white/30">•</span>
            <span>{formatRelativeTime(post.created_at)}</span>
          </div>
          {post.comment_count > 0 && (
            <span className="bg-white/10 px-2 py-0.5 rounded-full">
              {post.comment_count} {post.comment_count === 1 ? "comment" : "comments"}
            </span>
          )}
        </div>
      </div>
    </Link>
  );
}

function CreatePostModal({
  isOpen,
  onClose,
  onCreated,
}: {
  isOpen: boolean;
  onClose: () => void;
  onCreated: (post: CommunityPost) => void;
}) {
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [category, setCategory] = useState<string>("question");
  const [submitting, setSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) return;
    setSubmitting(true);
    try {
      const sessionId = getSessionId();
      const post = await createPost(sessionId, title.trim(), content.trim(), category);
      onCreated(post);
      setTitle("");
      setContent("");
      setCategory("question");
      onClose();
    } catch {
      alert("Failed to create post");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60">
      <div className="glass-card p-6 w-full max-w-lg">
        <h2 className="text-xl font-bold text-white mb-4">Create Post</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-white/60 text-sm mb-1">Category</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-sky-400"
            >
              <option value="question">Question</option>
              <option value="advice">Advice</option>
              <option value="update">Update</option>
              <option value="discussion">Discussion</option>
            </select>
          </div>
          <div>
            <label className="block text-white/60 text-sm mb-1">Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="What's on your mind?"
              className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white placeholder:text-white/40 focus:outline-none focus:border-sky-400"
            />
          </div>
          <div>
            <label className="block text-white/60 text-sm mb-1">Content</label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Share your thoughts..."
              rows={4}
              className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white placeholder:text-white/40 focus:outline-none focus:border-sky-400 resize-none"
            />
          </div>
          <div className="flex gap-3 justify-end">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white text-sm transition-all"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || !title.trim() || !content.trim()}
              className="btn-primary text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? "Posting..." : "Post"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function CommunityPage() {
  const [posts, setPosts] = useState<CommunityPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [sortBy, setSortBy] = useState("newest");

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search), 300);
    return () => clearTimeout(timer);
  }, [search]);

  const loadPosts = async (reset = false) => {
    try {
      const newOffset = reset ? 0 : offset;
      const fetched = await getCommunityFeed(
        20,
        newOffset,
        category || undefined,
        debouncedSearch || undefined,
        sortBy
      );
      if (reset) {
        setPosts(fetched);
        setOffset(20);
      } else {
        setPosts((prev) => [...prev, ...fetched]);
        setOffset((prev) => prev + 20);
      }
      setHasMore(fetched.length === 20);
    } catch {
      console.error("Failed to load posts");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setLoading(true);
    loadPosts(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [category, debouncedSearch, sortBy]);

  const handlePostCreated = (post: CommunityPost) => {
    setPosts((prev) => [post, ...prev]);
  };

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Background */}
      <div
        className="absolute inset-0 z-0"
        style={{
          backgroundImage: `url('https://plus.unsplash.com/premium_photo-1664443577580-dd2674e9d359?q=80&w=2071&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D')`,
          backgroundSize: "cover",
          backgroundPosition: "center",
        }}
      />
      <div className="absolute inset-0 z-0 bg-gradient-to-b from-slate-900/40 via-transparent to-slate-900/60" />

      {/* Header */}
      <header className="glass-header fixed top-0 left-0 right-0 z-50 px-6 py-4">
        <div className="mx-auto max-w-4xl flex items-center justify-between">
          <Link href="/" className="text-2xl font-bold text-white hover:text-white/80 transition-colors">
            PHOW
          </Link>
          <div className="flex items-center gap-3">
            <Link
              href="/dashboard"
              className="px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white text-sm font-medium transition-all border border-white/20"
            >
              Dashboard
            </Link>
            <button
              onClick={() => setShowModal(true)}
              className="btn-primary text-sm"
            >
              New Post
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative z-10 pt-24 pb-12 px-6">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold text-white mb-6">Community</h1>

          {/* Search */}
          <div className="mb-4">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search posts..."
              className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2.5 text-white placeholder:text-white/40 focus:outline-none focus:border-sky-400"
            />
          </div>

          {/* Category Tabs + Sort */}
          <div className="flex items-center justify-between gap-4 mb-6">
            <div className="flex gap-2 overflow-x-auto pb-2">
              {CATEGORIES.map((cat) => (
                <button
                  key={cat.id ?? "all"}
                  onClick={() => setCategory(cat.id)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${
                    category === cat.id
                      ? "bg-sky-500/30 text-sky-400 border border-sky-500/50"
                      : "bg-white/10 text-white/70 border border-white/10 hover:bg-white/20"
                  }`}
                >
                  {cat.label}
                </button>
              ))}
            </div>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-sky-400"
            >
              {SORT_OPTIONS.map((opt) => (
                <option key={opt.id} value={opt.id}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {/* Posts */}
          {loading ? (
            <div className="text-center py-12 text-white/60">Loading...</div>
          ) : posts.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-white/50 mb-4">No posts yet. Be the first to share!</p>
              <button onClick={() => setShowModal(true)} className="btn-primary text-sm">
                Create Post
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {posts.map((post) => (
                <PostCard key={post.id} post={post} />
              ))}
              {hasMore && (
                <button
                  onClick={() => loadPosts(false)}
                  className="w-full py-3 text-white/60 hover:text-white text-sm transition-colors"
                >
                  Load more
                </button>
              )}
            </div>
          )}
        </div>
      </main>

      <CreatePostModal isOpen={showModal} onClose={() => setShowModal(false)} onCreated={handlePostCreated} />
    </div>
  );
}

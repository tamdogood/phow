"use client";

import { useState, useEffect, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { getPost, addComment, deletePost, deleteComment, updatePost } from "@/lib/api";
import { getSessionId } from "@/lib/session";
import { PostWithComments, PostComment } from "@/types";

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

function CommentItem({
  comment,
  sessionId,
  onDelete,
}: {
  comment: PostComment;
  sessionId: string;
  onDelete: (id: string) => void;
}) {
  const authorName = comment.business_profiles?.business_name || "Anonymous";
  const isOwner = comment.session_id === sessionId;

  return (
    <div className="py-4 border-b border-white/10 last:border-0">
      <div className="flex items-center justify-between mb-2">
        <span className="text-white/60 text-sm">{authorName}</span>
        <div className="flex items-center gap-3">
          <span className="text-white/40 text-xs">{formatRelativeTime(comment.created_at)}</span>
          {isOwner && (
            <button
              onClick={() => onDelete(comment.id)}
              className="text-red-400/70 hover:text-red-400 text-xs"
            >
              Delete
            </button>
          )}
        </div>
      </div>
      <p className="text-white/80">{comment.content}</p>
    </div>
  );
}

export default function PostPage({ params }: { params: Promise<{ postId: string }> }) {
  const { postId } = use(params);
  const router = useRouter();
  const [post, setPost] = useState<PostWithComments | null>(null);
  const [loading, setLoading] = useState(true);
  const [commentText, setCommentText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editTitle, setEditTitle] = useState("");
  const [editContent, setEditContent] = useState("");
  const sessionId = getSessionId();

  useEffect(() => {
    async function load() {
      try {
        const data = await getPost(postId);
        setPost(data);
      } catch {
        console.error("Failed to load post");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [postId]);

  const handleAddComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!commentText.trim() || !post) return;
    setSubmitting(true);
    try {
      const comment = await addComment(post.id, sessionId, commentText.trim());
      setPost((prev) => prev ? { ...prev, comments: [comment, ...prev.comments] } : prev);
      setCommentText("");
    } catch {
      alert("Failed to add comment");
    } finally {
      setSubmitting(false);
    }
  };

  const startEditing = () => {
    if (!post) return;
    setEditTitle(post.title);
    setEditContent(post.content);
    setEditing(true);
  };

  const handleEditPost = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!post || !editTitle.trim() || !editContent.trim()) return;
    setSubmitting(true);
    try {
      await updatePost(post.id, sessionId, editTitle.trim(), editContent.trim());
      setPost((prev) => prev ? { ...prev, title: editTitle.trim(), content: editContent.trim() } : prev);
      setEditing(false);
    } catch {
      alert("Failed to update post");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeletePost = async () => {
    if (!post || !confirm("Delete this post?")) return;
    try {
      await deletePost(post.id, sessionId);
      router.push("/community");
    } catch {
      alert("Failed to delete post");
    }
  };

  const handleDeleteComment = async (commentId: string) => {
    if (!confirm("Delete this comment?")) return;
    try {
      await deleteComment(commentId, sessionId);
      setPost((prev) => prev ? { ...prev, comments: prev.comments.filter((c) => c.id !== commentId) } : prev);
    } catch {
      alert("Failed to delete comment");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-white/60">Loading...</div>
      </div>
    );
  }

  if (!post) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-white/60 mb-4">Post not found</p>
          <Link href="/community" className="text-sky-400 hover:underline">
            Back to Community
          </Link>
        </div>
      </div>
    );
  }

  const authorName = post.business_profiles?.business_name || "Anonymous";
  const isOwner = post.session_id === sessionId;

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
          <Link
            href="/community"
            className="px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white text-sm font-medium transition-all border border-white/20"
          >
            Back to Community
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative z-10 pt-24 pb-12 px-6">
        <div className="max-w-4xl mx-auto">
          {/* Post */}
          <div className="glass-card p-6 mb-6">
            {editing ? (
              <form onSubmit={handleEditPost} className="space-y-4">
                <input
                  type="text"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white text-xl font-bold focus:outline-none focus:border-sky-400"
                />
                <textarea
                  value={editContent}
                  onChange={(e) => setEditContent(e.target.value)}
                  rows={6}
                  className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white/80 focus:outline-none focus:border-sky-400 resize-none"
                />
                <div className="flex gap-3 justify-end">
                  <button
                    type="button"
                    onClick={() => setEditing(false)}
                    className="px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white text-sm"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting || !editTitle.trim() || !editContent.trim()}
                    className="btn-primary text-sm disabled:opacity-50"
                  >
                    {submitting ? "Saving..." : "Save"}
                  </button>
                </div>
              </form>
            ) : (
              <>
                <div className="flex items-start justify-between gap-3 mb-3">
                  <h1 className="text-2xl font-bold text-white">{post.title}</h1>
                  <CategoryBadge category={post.category} />
                </div>
                <div className="flex items-center gap-3 text-sm text-white/50 mb-4">
                  <span>{authorName}</span>
                  <span>•</span>
                  <span>{formatRelativeTime(post.created_at)}</span>
                  {isOwner && (
                    <>
                      <span>•</span>
                      <button onClick={startEditing} className="text-sky-400/70 hover:text-sky-400">
                        Edit
                      </button>
                      <span>•</span>
                      <button onClick={handleDeletePost} className="text-red-400/70 hover:text-red-400">
                        Delete
                      </button>
                    </>
                  )}
                </div>
                <p className="text-white/80 whitespace-pre-wrap">{post.content}</p>
              </>
            )}
          </div>

          {/* Comment Form */}
          <div className="glass-card p-6 mb-6">
            <h2 className="text-lg font-semibold text-white mb-4">Add a Comment</h2>
            <form onSubmit={handleAddComment} className="flex gap-3">
              <input
                type="text"
                value={commentText}
                onChange={(e) => setCommentText(e.target.value)}
                placeholder="Share your advice or thoughts..."
                className="flex-1 bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder:text-white/40 focus:outline-none focus:border-sky-400"
              />
              <button
                type="submit"
                disabled={submitting || !commentText.trim()}
                className="btn-primary text-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting ? "..." : "Comment"}
              </button>
            </form>
          </div>

          {/* Comments */}
          <div className="glass-card p-6">
            <h2 className="text-lg font-semibold text-white mb-4">
              Comments ({post.comments.length})
            </h2>
            {post.comments.length === 0 ? (
              <p className="text-white/50 text-center py-4">No comments yet. Be the first to respond!</p>
            ) : (
              <div>
                {post.comments.map((comment) => (
                  <CommentItem
                    key={comment.id}
                    comment={comment}
                    sessionId={sessionId}
                    onDelete={handleDeleteComment}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

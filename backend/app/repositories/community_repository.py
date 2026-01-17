from typing import Any
from .base import BaseRepository


class CommunityPostRepository(BaseRepository):
    """Repository for community post database operations."""

    async def create(
        self,
        session_id: str,
        title: str,
        content: str,
        category: str | None = None,
        user_id: str | None = None,
        business_profile_id: str | None = None,
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        result = (
            self.db.table("community_posts")
            .insert({
                "session_id": session_id,
                "title": title,
                "content": content,
                "category": category,
                "user_id": user_id,
                "business_profile_id": business_profile_id,
                "metadata": metadata,
            })
            .execute()
        )
        return result.data[0] if result.data else {}

    async def get_by_id(self, post_id: str) -> dict[str, Any] | None:
        result = (
            self.db.table("community_posts")
            .select("*, business_profiles(business_name, business_type)")
            .eq("id", post_id)
            .execute()
        )
        return result.data[0] if result.data else None

    async def get_feed(
        self,
        limit: int = 20,
        offset: int = 0,
        category: str | None = None,
        search: str | None = None,
        sort_by: str = "newest",
    ) -> list[dict[str, Any]]:
        query = self.db.table("community_posts").select(
            "*, business_profiles(business_name, business_type), post_comments(count)"
        )
        if category:
            query = query.eq("category", category)
        if search:
            query = query.or_(f"title.ilike.%{search}%,content.ilike.%{search}%")
        if sort_by == "oldest":
            query = query.order("created_at", desc=False)
        else:
            query = query.order("created_at", desc=True)
        query = query.range(offset, offset + limit - 1)
        result = query.execute()
        posts = result.data or []
        # Transform comment count and handle most_comments sort
        for post in posts:
            count_data = post.pop("post_comments", [])
            post["comment_count"] = count_data[0]["count"] if count_data else 0
        if sort_by == "most_comments":
            posts.sort(key=lambda p: p["comment_count"], reverse=True)
        return posts

    async def get_by_session(self, session_id: str, limit: int = 50) -> list[dict[str, Any]]:
        result = (
            self.db.table("community_posts")
            .select("*, business_profiles(business_name, business_type)")
            .eq("session_id", session_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []

    async def update(
        self, post_id: str, title: str | None = None, content: str | None = None
    ) -> dict[str, Any] | None:
        updates = {}
        if title is not None:
            updates["title"] = title
        if content is not None:
            updates["content"] = content
        if not updates:
            return None
        result = (
            self.db.table("community_posts")
            .update(updates)
            .eq("id", post_id)
            .execute()
        )
        return result.data[0] if result.data else None

    async def delete(self, post_id: str) -> bool:
        result = self.db.table("community_posts").delete().eq("id", post_id).execute()
        return bool(result.data)

    async def verify_ownership(self, post_id: str, session_id: str) -> bool:
        result = (
            self.db.table("community_posts")
            .select("id")
            .eq("id", post_id)
            .eq("session_id", session_id)
            .execute()
        )
        return bool(result.data)


class PostCommentRepository(BaseRepository):
    """Repository for post comment database operations."""

    async def create(
        self,
        post_id: str,
        session_id: str,
        content: str,
        user_id: str | None = None,
        business_profile_id: str | None = None,
    ) -> dict[str, Any]:
        result = (
            self.db.table("post_comments")
            .insert({
                "post_id": post_id,
                "session_id": session_id,
                "content": content,
                "user_id": user_id,
                "business_profile_id": business_profile_id,
            })
            .execute()
        )
        return result.data[0] if result.data else {}

    async def get_by_post(self, post_id: str) -> list[dict[str, Any]]:
        result = (
            self.db.table("post_comments")
            .select("*, business_profiles(business_name, business_type)")
            .eq("post_id", post_id)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []

    async def delete(self, comment_id: str) -> bool:
        result = self.db.table("post_comments").delete().eq("id", comment_id).execute()
        return bool(result.data)

    async def verify_ownership(self, comment_id: str, session_id: str) -> bool:
        result = (
            self.db.table("post_comments")
            .select("id")
            .eq("id", comment_id)
            .eq("session_id", session_id)
            .execute()
        )
        return bool(result.data)

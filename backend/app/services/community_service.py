"""Service for managing community posts and comments."""

from typing import Any
from supabase import Client
from ..repositories.community_repository import CommunityPostRepository, PostCommentRepository
from ..repositories.business_profile_repository import BusinessProfileRepository


class CommunityService:
    """Service for community operations."""

    def __init__(self, db: Client):
        self.post_repo = CommunityPostRepository(db)
        self.comment_repo = PostCommentRepository(db)
        self.profile_repo = BusinessProfileRepository(db)

    async def create_post(
        self,
        session_id: str,
        title: str,
        content: str,
        category: str | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a new community post, auto-linking business profile if exists."""
        profile = await self.profile_repo.get_latest_by_session(session_id)
        business_profile_id = profile["id"] if profile else None

        return await self.post_repo.create(
            session_id=session_id,
            title=title,
            content=content,
            category=category,
            user_id=user_id,
            business_profile_id=business_profile_id,
        )

    async def get_feed(
        self,
        limit: int = 20,
        offset: int = 0,
        category: str | None = None,
        search: str | None = None,
        sort_by: str = "newest",
    ) -> list[dict[str, Any]]:
        """Get paginated community feed."""
        return await self.post_repo.get_feed(
            limit=limit, offset=offset, category=category, search=search, sort_by=sort_by
        )

    async def get_post(self, post_id: str) -> dict[str, Any] | None:
        """Get post with all comments."""
        post = await self.post_repo.get_by_id(post_id)
        if not post:
            return None
        comments = await self.comment_repo.get_by_post(post_id)
        post["comments"] = comments
        return post

    async def update_post(
        self,
        post_id: str,
        session_id: str,
        title: str | None = None,
        content: str | None = None,
    ) -> dict[str, Any] | None:
        """Update a post if owned by session."""
        if not await self.post_repo.verify_ownership(post_id, session_id):
            return None
        return await self.post_repo.update(post_id, title=title, content=content)

    async def delete_post(self, post_id: str, session_id: str) -> bool:
        """Delete a post if owned by session."""
        if not await self.post_repo.verify_ownership(post_id, session_id):
            return False
        return await self.post_repo.delete(post_id)

    async def add_comment(
        self,
        post_id: str,
        session_id: str,
        content: str,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """Add a comment to a post, auto-linking business profile if exists."""
        profile = await self.profile_repo.get_latest_by_session(session_id)
        business_profile_id = profile["id"] if profile else None

        return await self.comment_repo.create(
            post_id=post_id,
            session_id=session_id,
            content=content,
            user_id=user_id,
            business_profile_id=business_profile_id,
        )

    async def delete_comment(self, comment_id: str, session_id: str) -> bool:
        """Delete a comment if owned by session."""
        if not await self.comment_repo.verify_ownership(comment_id, session_id):
            return False
        return await self.comment_repo.delete(comment_id)

    async def get_my_posts(self, session_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """Get posts created by a session."""
        return await self.post_repo.get_by_session(session_id, limit)

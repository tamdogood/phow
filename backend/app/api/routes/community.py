from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from supabase import Client
from ..deps import get_supabase
from ...services.community_service import CommunityService

router = APIRouter(prefix="/community", tags=["community"])


class CreatePostRequest(BaseModel):
    session_id: str
    title: str
    content: str
    category: str | None = None
    user_id: str | None = None


class CreateCommentRequest(BaseModel):
    session_id: str
    content: str
    user_id: str | None = None


class UpdatePostRequest(BaseModel):
    session_id: str
    title: str | None = None
    content: str | None = None


class DeleteRequest(BaseModel):
    session_id: str


def get_community_service(db: Client = Depends(get_supabase)) -> CommunityService:
    return CommunityService(db)


@router.get("/posts")
async def get_feed(
    limit: int = 20,
    offset: int = 0,
    category: str | None = None,
    search: str | None = None,
    sort_by: str = "newest",
    service: CommunityService = Depends(get_community_service),
):
    """Get paginated community feed."""
    posts = await service.get_feed(
        limit=limit, offset=offset, category=category, search=search, sort_by=sort_by
    )
    return {"posts": posts}


@router.post("/posts")
async def create_post(
    request: CreatePostRequest,
    service: CommunityService = Depends(get_community_service),
):
    """Create a new community post."""
    post = await service.create_post(
        session_id=request.session_id,
        title=request.title,
        content=request.content,
        category=request.category,
        user_id=request.user_id,
    )
    return {"post": post}


@router.get("/posts/{post_id}")
async def get_post(
    post_id: str,
    service: CommunityService = Depends(get_community_service),
):
    """Get a post with all comments."""
    post = await service.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"post": post}


@router.patch("/posts/{post_id}")
async def update_post(
    post_id: str,
    request: UpdatePostRequest,
    service: CommunityService = Depends(get_community_service),
):
    """Update a post (owner only)."""
    post = await service.update_post(
        post_id, request.session_id, title=request.title, content=request.content
    )
    if not post:
        raise HTTPException(status_code=403, detail="Not authorized to update this post")
    return {"post": post}


@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: str,
    request: DeleteRequest,
    service: CommunityService = Depends(get_community_service),
):
    """Delete a post (owner only)."""
    deleted = await service.delete_post(post_id, request.session_id)
    if not deleted:
        raise HTTPException(status_code=403, detail="Not authorized to delete this post")
    return {"deleted": True}


@router.post("/posts/{post_id}/comments")
async def add_comment(
    post_id: str,
    request: CreateCommentRequest,
    service: CommunityService = Depends(get_community_service),
):
    """Add a comment to a post."""
    comment = await service.add_comment(
        post_id=post_id,
        session_id=request.session_id,
        content=request.content,
        user_id=request.user_id,
    )
    return {"comment": comment}


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: str,
    request: DeleteRequest,
    service: CommunityService = Depends(get_community_service),
):
    """Delete a comment (owner only)."""
    deleted = await service.delete_comment(comment_id, request.session_id)
    if not deleted:
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")
    return {"deleted": True}


@router.get("/my-posts")
async def get_my_posts(
    session_id: str,
    limit: int = 50,
    service: CommunityService = Depends(get_community_service),
):
    """Get posts created by the current session."""
    posts = await service.get_my_posts(session_id, limit)
    return {"posts": posts}

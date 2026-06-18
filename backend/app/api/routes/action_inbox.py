from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from supabase import Client
from ..deps import get_supabase
from ...services.action_inbox_service import ActionInboxService

router = APIRouter(prefix="/action-inbox", tags=["action-inbox"])


class CreateActionRequest(BaseModel):
    business_profile_id: str
    text: str
    session_id: str | None = None
    user_id: str | None = None


def get_action_inbox_service(db: Client = Depends(get_supabase)) -> ActionInboxService:
    return ActionInboxService(db)


@router.get("")
async def list_actions(
    business_profile_id: str,
    status: str | None = "open",
    service: ActionInboxService = Depends(get_action_inbox_service),
):
    return {"items": await service.list_items(business_profile_id, status)}


@router.post("")
async def create_action(
    request: CreateActionRequest,
    service: ActionInboxService = Depends(get_action_inbox_service),
):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Action text is required")
    item = await service.create(
        request.business_profile_id, request.text, request.session_id, request.user_id
    )
    return {"item": item}


@router.post("/{item_id}/{action}")
async def update_action(
    item_id: str,
    action: str,
    service: ActionInboxService = Depends(get_action_inbox_service),
):
    status = {"done": "done", "dismiss": "dismissed", "reopen": "open"}.get(action)
    if not status:
        raise HTTPException(status_code=400, detail="Unknown action")
    item = await service.update_status(item_id, status)
    if not item:
        raise HTTPException(status_code=404, detail="Action not found")
    return {"item": item}

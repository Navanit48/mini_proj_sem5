from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_user
from app.schemas.assistant import (
    AssistantMessageCreate, AssistantReplyResponse, ConversationCreate,
    ConversationListResponse, ConversationResponse,
)
from app.services.ai.assistant_service import AssistantService
from app.utils.supabase_client import get_supabase_client

router = APIRouter()


def _service() -> AssistantService:
    return AssistantService(get_supabase_client())


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(user=Depends(get_current_user)):
    conversations = _service().list_conversations(user.id)
    return {"conversations": conversations, "total": len(conversations)}


@router.post("/conversations", response_model=ConversationResponse, status_code=201)
async def create_conversation(data: ConversationCreate, user=Depends(get_current_user)):
    conversation = _service().create_conversation(user.id, data.title)
    return {"conversation_id": conversation["id"], "messages": []}


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str, user=Depends(get_current_user)):
    messages = _service().get_conversation(user.id, conversation_id)
    return {"conversation_id": conversation_id, "messages": messages}


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=AssistantReplyResponse,
)
async def send_message(
    conversation_id: str,
    data: AssistantMessageCreate,
    user=Depends(get_current_user),
):
    if not data.content.strip():
        raise HTTPException(status_code=422, detail="Message cannot be empty")
    response = _service().send_message(user.id, conversation_id, data.content)
    return {"conversation_id": conversation_id, **response}


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(conversation_id: str, user=Depends(get_current_user)):
    _service().delete_conversation(user.id, conversation_id)

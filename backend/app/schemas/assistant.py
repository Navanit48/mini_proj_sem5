from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, max_length=120)


class AssistantMessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class AssistantMessage(BaseModel):
    id: str
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime | str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConversationSummary(BaseModel):
    id: str
    title: str
    created_at: datetime | str
    updated_at: datetime | str


class ConversationListResponse(BaseModel):
    conversations: list[ConversationSummary]
    total: int


class ConversationResponse(BaseModel):
    conversation_id: str
    messages: list[AssistantMessage]


class AssistantReplyResponse(BaseModel):
    conversation_id: str
    user_message: AssistantMessage
    assistant_message: AssistantMessage

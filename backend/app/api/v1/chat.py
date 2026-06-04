"""Streaming AI financial assistant endpoint using Server-Sent Events."""
import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from openai import AsyncOpenAI
from app.core.config import settings
from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/chat", tags=["AI Assistant"])

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

SYSTEM_PROMPT = """You are FinSight AI, an expert personal financial advisor assistant.
You help users understand their spending patterns, budget their money wisely, 
identify saving opportunities, and make sound financial decisions.

Guidelines:
- Be concise, warm, and actionable
- Always use the user's currency when discussing amounts
- Never give specific investment advice about individual securities
- Recommend professional financial advisors for complex tax/legal questions
- Focus on practical, achievable recommendations
- Use clear numbers and percentages when discussing budgets and savings
"""


class ChatMessage(BaseModel):
    role: str  # user | assistant
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    context: Optional[dict] = None  # user financial summary injected by frontend


async def stream_chat(messages: List[ChatMessage], context: Optional[dict]):
    system = SYSTEM_PROMPT
    if context:
        system += f"\n\nUser's current financial context:\n{json.dumps(context, indent=2)}"

    formatted = [{"role": "system", "content": system}]
    for msg in messages:
        formatted.append({"role": msg.role, "content": msg.content})

    async with client.chat.completions.stream(
        model=settings.OPENAI_MODEL,
        messages=formatted,
        max_tokens=1000,
        temperature=0.7,
    ) as stream:
        async for text in stream.text_stream:
            yield f"data: {json.dumps({'delta': text})}\n\n"
    yield "data: [DONE]\n\n"


@router.post("")
async def chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_active_user),
):
    return StreamingResponse(
        stream_chat(payload.messages, payload.context),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

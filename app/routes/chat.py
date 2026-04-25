from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_limiter.depends import RateLimiter
from fastapi.responses import StreamingResponse
from sqlalchemy import select
import json


from app.db import get_db
from app.schemas import ChatRequest, ChatResponse
from app.services.chat_service import chat_with_ai, prepare_chat_context, stream_ai_response
from app.core.deps import get_current_user
from app.core.rate_limiter import user_identifier
from app.models import Chat, Message, User

router = APIRouter(prefix="/chat", tags=["AI Chat"])


@router.post("/", response_model=ChatResponse)
async def chat(
    request: Request,
    chat_request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
    rate_limit: None = Depends(RateLimiter(times=5, seconds=60, identifier=user_identifier))
):
    # 🔥 store user_id for limiter
    request.state.user_id = user_id

    chat_request.user_id = user_id

    return await chat_with_ai(chat_request, db)

@router.post("/stream")
async def stream_chat(
    request: Request,
    chat_request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    chat_request.user_id = user_id

    # 1. Faster context prep (service is now optimized)
    history, chat_id, _ = await prepare_chat_context(chat_request, db)

    async def event_generator():
        full_response = ""
        
        # 🔥 First chunk sends metadata (chat_id)
        yield f"data: {json.dumps({'chat_id': str(chat_id), 'chunk': ''})}\n\n"

        async for chunk in stream_ai_response(history):
            full_response += chunk
            # SSE format requires "data: ...\n\n"
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        
        # 2. SAVE AI MESSAGE to DB after stream finishes
        if full_response.strip():
            ai_msg = Message(
                chat_id=chat_id,
                role="assistant",
                content=full_response
            )
            db.add(ai_msg)
            await db.commit()

        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/history")
async def get_chat_history(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    # 🛡️ Tiered Access: Only Pro users get chat history
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()

    if not user or user.plan == "free":
        return []

    result = await db.execute(
        select(Chat)
        .where(Chat.user_id == user_id)
        .order_by(Chat.created_at.desc())
    )

    chats = result.scalars().all()

    return [
        {
            "chat_id": str(chat.id),
            "title": chat.summary or "New Chat"
        }
        for chat in chats
    ]

@router.get("/{chat_id}")
async def get_chat_messages(
    chat_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    result = await db.execute(
        select(Chat).where(Chat.id == chat_id)
    )
    chat = result.scalar_one_or_none()

    if not chat:
        return []

    if str(chat.user_id) != str(user_id):
        return []

    result = await db.execute(
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at.asc())
    )

    messages = result.scalars().all()

    return [
        {
            "role": msg.role,
            "text": msg.content
        }
        for msg in messages
    ]

@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    result = await db.execute(
        select(Chat).where(Chat.id == chat_id)
    )
    chat = result.scalar_one_or_none()

    if not chat:
        return {"success": False, "message": "Chat not found"}

    if str(chat.user_id) != str(user_id):
        return {"success": False, "message": "Unauthorized"}

    await db.delete(chat)
    await db.commit()

    return {"success": True, "message": "Chat deleted"}

import hashlib
from fastapi import HTTPException
from sqlalchemy import select
from groq import AsyncGroq

from app.core.config import settings
from app.models import Chat, Message, User
from app.schemas import ChatRequest, ChatResponse
from app.core.redis import redis_client, ArqManager
from app.services.quota_service import check_and_increment_quota
from app.services.rag_service import search_relevant_context

client = AsyncGroq(api_key=settings.GROQ_API_KEY)

# Enhanced System Prompt for RAG
SYSTEM_PROMPT = """
You are AMI, a smart personal assistant. 
- You have access to the user's "Knowledge Base" (uploaded files).
- If the user asks about their files, prioritize the provided context above everything.
- If the question is general (e.g., 'What is 2+2?'), answer it normally using your own knowledge.
- If the context is relevant but doesn't fully answer the question, combine the context with your knowledge and provide the answer based on various report on web.
- Keep citations subtle (e.g., 'Based on your files...').
- Be concise (2-4 lines).
"""

async def get_ai_response(messages):
    response = await client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        max_tokens=400,
        temperature=0.5
    )
    return response.choices[0].message.content

async def stream_ai_response(messages):
    """Yields AI response chunks word-by-word using Groq streaming."""
    stream = await client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        max_tokens=400,
        temperature=0.7,
        stream=True
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta

async def summarize_messages(messages):
    prompt = [
        {"role": "system", "content": "Condense this chat into 1-2 memory-tags."},
        {"role": "user", "content": str([{"r": m.get('role'), "c": m.get('content', '')[:100]} for m in messages])}
    ]

    response = await client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=prompt,
        max_tokens=100,
        temperature=0.5
    )

    return response.choices[0].message.content

async def prepare_chat_context(data: ChatRequest, db):
    """
    Optimized for Speed: Use summaries to minimize message window and RAG for knowledge.
    """
    if not data.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    user_input = data.message.strip()[:400]

    # 1. USER VALIDATION
    result = await db.execute(select(User).where(User.id == data.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. QUOTA CHECK
    await check_and_increment_quota(str(user.id), user.plan)

    # 3. CHAT VALIDATION / CREATE
    chat = None
    if data.chat_id:
        result = await db.execute(select(Chat).where(Chat.id == data.chat_id))
        chat = result.scalar_one_or_none()
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        if str(chat.user_id) != str(data.user_id):
            raise HTTPException(status_code=403, detail="Unauthorized access")

    if not chat:
        title = user_input[:100]
        chat = Chat(user_id=data.user_id, summary=title)
        db.add(chat)
        await db.commit()
        await db.refresh(chat)

    chat_id = chat.id

    # 4. SAVE USER MESSAGE
    user_msg = Message(chat_id=chat_id, role="user", content=user_input)
    db.add(user_msg)
    await db.commit()

    # 5. FETCH RELEVANT KNOWLEDGE (RAG)
    # This is the "Sharp Memory" part
    knowledge_context = await search_relevant_context(user_input, str(user.id), db)

    # 6. FETCH RECENT HISTORY
    limit = 5 if user.plan == "free" else 15
    result = await db.execute(
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    all_msgs = result.scalars().all()
    all_msgs = list(reversed(all_msgs))

    # 7. BUILD HISTORY LIST
    history_list = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    if knowledge_context:
        history_list.append({
            "role": "system", 
            "content": f"Knowledge Base Context (Use this to answer if relevant):\n{knowledge_context}"
        })
    
    if user.plan == "free":
        recent_messages = all_msgs[-3:] 
    else:
        if chat.summary:
            history_list.append({
                "role": "system",
                "content": f"Memory recall of previous topics: {chat.summary}"
            })
            recent_messages = all_msgs[-6:] 
        else:
            recent_messages = all_msgs[-11:]

    history_list += [
        {"role": msg.role, "content": msg.content}
        for msg in recent_messages[:-1]
    ]
    history_list.append({"role": "user", "content": user_input})

    return history_list, chat_id, user_input, bool(knowledge_context)

async def chat_with_ai(data: ChatRequest, db):
    """Standard non-streaming chat."""
    user_input = data.message.strip()[:400]
    history, chat_id, _, _ = await prepare_chat_context(data, db)

    try:
        ai_reply = await get_ai_response(history)
    except Exception:
        raise HTTPException(status_code=500, detail="AI service failed")

    ai_msg = Message(chat_id=chat_id, role="assistant", content=ai_reply)
    db.add(ai_msg)
    await db.commit()

    return ChatResponse(
        chat_id=chat_id,
        user_message=user_input,
        ai_response=ai_reply
    )
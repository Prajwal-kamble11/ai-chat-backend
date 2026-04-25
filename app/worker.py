from dotenv import load_dotenv
from arq.connections import RedisSettings
from sqlalchemy import select

from app.core.config import settings
from app.db import async_sessionmaker
from app.models import Chat
from app.services.chat_service import summarize_messages

# Load environment before anything else
load_dotenv()

redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)

async def update_summary_task(ctx, chat_id: str, messages_data: list):
    """
    Background job to summarize the last N messages using AsyncGroq.
    Arguments:
    - chat_id (str): UUID of the chat
    - messages_data (list): List of dicts representing messages [{"role": "user", "content": "..."}]
    """
    
    # 1. Ask LLM to summarize
    try:
        summary_text = await summarize_messages(messages_data)
    except Exception as e:
        print(f"Error summarizing chat {chat_id}: {e}")
        return

    # 2. Update DB
    async with async_sessionmaker() as db:
        result = await db.execute(
            select(Chat).where(Chat.id == chat_id)
        )
        chat = result.scalar_one_or_none()

        if chat:
            chat.summary = summary_text
            await db.commit()
            print(f"✅ Successfully updated summary for chat {chat_id}")


class WorkerSettings:
    functions = [update_summary_task]
    redis_settings = redis_settings

from dotenv import load_dotenv
from arq.connections import RedisSettings
from sqlalchemy import select
import json

from app.core.config import settings
from app.db import SessionLocal
from app.models import Chat, File, DocumentChunk
from app.services.chat_service import summarize_messages
from app.services.file_service import extract_text_from_pdf, extract_text_from_txt, chunk_text
from app.services.vector_service import get_batch_embeddings

# Load environment before anything else
load_dotenv()

redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)

async def update_summary_task(ctx, chat_id: str, messages_data: list):
    """
    Background job to summarize the last N messages using AsyncGroq.
    """
    try:
        summary_text = await summarize_messages(messages_data)
    except Exception as e:
        print(f"Error summarizing chat {chat_id}: {e}")
        return

    async with SessionLocal() as db:
        result = await db.execute(
            select(Chat).where(Chat.id == chat_id)
        )
        chat = result.scalar_one_or_none()

        if chat:
            chat.summary = summary_text
            await db.commit()
            print(f"✅ Successfully updated summary for chat {chat_id}")

async def process_file_task(ctx, file_id: str, file_content: bytes, file_type: str, user_id: str):
    """
    Background job to process uploaded files:
    1. Extract text
    2. Chunk text
    3. Generate embeddings
    4. Save to vector DB
    """
    print(f"📄 Processing file {file_id} for user {user_id}...")

    try:
        # 1. Extract Text
        if "pdf" in file_type.lower():
            text = extract_text_from_pdf(file_content)
        else:
            text = extract_text_from_txt(file_content)

        if not text.strip():
            print(f"⚠️ No text extracted from file {file_id}")
            return

        # 2. Chunk Text
        chunks = chunk_text(text)
        print(f"✂️ Created {len(chunks)} chunks for file {file_id}")

        # 3. Generate Embeddings (Batch)
        # Using sentence-transformers (local)
        embeddings = get_batch_embeddings(chunks)

        # 4. Save to DB
        async with SessionLocal() as db:
            for i, (chunk_text_val, embedding) in enumerate(zip(chunks, embeddings)):
                doc_chunk = DocumentChunk(
                    file_id=file_id,
                    user_id=user_id,
                    content=chunk_text_val,
                    embedding=embedding,
                    extra_metadata=json.dumps({"chunk_index": i})
                )
                db.add(doc_chunk)
            
            await db.commit()
            print(f"🚀 Successfully indexed {len(chunks)} chunks for file {file_id}")

    except Exception as e:
        print(f"❌ Error processing file {file_id}: {e}")

class WorkerSettings:
    functions = [update_summary_task, process_file_task]
    redis_settings = redis_settings

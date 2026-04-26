from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db import get_db
from app.models import File, User
from app.schemas import FileResponse
from app.core.deps import get_current_user
from app.core.redis import ArqManager

router = APIRouter(prefix="/files", tags=["File Management"])

@router.post("/upload", response_model=FileResponse)
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    # 1. Validation
    if not file.filename.lower().endswith(('.pdf', '.txt')):
        raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported.")

    # 2. Read content
    content = await file.read()
    file_size = len(content)

    if file_size > 5 * 1024 * 1024: # 5MB limit
        raise HTTPException(status_code=400, detail="File too large. Max 5MB.")

    # 3. Save File Record to DB
    new_file = File(
        user_id=user_id,
        filename=file.filename,
        file_type=file.content_type,
        file_size=file_size
    )
    db.add(new_file)
    await db.commit()
    await db.refresh(new_file)

    # 4. Queue Background Task for Processing (RAG Pipeline)
    try:
        await ArqManager.pool.enqueue_job(
            "process_file_task",
            str(new_file.id),
            content,
            file.content_type,
            str(user_id)
        )
    except Exception as e:
        print(f"Failed to queue file processing: {e}")
        # Note: File record is saved, but processing might be delayed

    return new_file

@router.get("/", response_model=List[FileResponse])
async def list_user_files(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    result = await db.execute(
        select(File).where(File.user_id == user_id).order_by(File.created_at.desc())
    )
    return result.scalars().all()

@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    result = await db.execute(
        select(File).where(File.id == file_id)
    )
    file_record = result.scalar_one_or_none()

    if not file_record or str(file_record.user_id) != str(user_id):
        raise HTTPException(status_code=404, detail="File not found")

    await db.delete(file_record)
    await db.commit()
    return {"success": True, "message": "File and its knowledge chunks deleted."}

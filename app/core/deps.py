from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import decode_clerk_token
from app.db import get_db
from app.models import User

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    token = credentials.credentials
    payload = decode_clerk_token(token)

    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid Clerk token")

    clerk_id = payload["sub"]

    # ✅ Lookup the user by clerk_user_id
    result = await db.execute(select(User).where(User.clerk_user_id == clerk_id))
    user = result.scalar_one_or_none()

    if not user:
        # Auto-create user from Clerk token if missing in our DB, so app won't break
        email_claim = payload.get("email") or f"{clerk_id}@placeholder.clerk.com"
        user = User(clerk_user_id=clerk_id, email=email_claim)
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # Return internal UUID as string, which chat_service needs for user.id
    return str(user.id)
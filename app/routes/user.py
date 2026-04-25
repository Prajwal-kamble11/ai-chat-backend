from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse

from app.core.deps import get_current_user


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_me(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/", response_model=UserResponse)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):

    if not user.clerk_user_id.strip():
        raise HTTPException(status_code=400, detail="Invalid clerk_user_id")

    # Check if user exists
    result = await db.execute(
        select(User).where(User.clerk_user_id == user.clerk_user_id)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        return existing_user

    # Create new user
    new_user = User(
        clerk_user_id=user.clerk_user_id,
        email=user.email
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user
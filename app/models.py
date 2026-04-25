import uuid
from datetime import datetime
from sqlalchemy.sql import func

from sqlalchemy import Column, String, ForeignKey, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db import Base


# 🔹 USER TABLE
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clerk_user_id = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    plan = Column(String, default="free")
    subscription_expires_at = Column(DateTime, nullable=True)

    # ✅ Relationship (1 user → many chats)
    chats = relationship("Chat", back_populates="user", cascade="all, delete")


# 🔹 CHAT TABLE
class Chat(Base):
    __tablename__ = "chats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    summary = Column(String(255), nullable=True)

    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="chats")
    messages = relationship(
        "Message",
        back_populates="chat",
        cascade="all, delete"
    )

# 🔹 MESSAGE TABLE
class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(UUID(as_uuid=True),ForeignKey("chats.id", ondelete="CASCADE"),nullable=False, index=True )

    role = Column(String(20), nullable=False)
    content = Column(String(1000), nullable=False)

    # ✅ NEW: timestamp (VERY IMPORTANT 🔥)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # ✅ Relationship
    chat = relationship("Chat", back_populates="messages")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Integer, nullable=False)
    status = Column(String, default="success")
    created_at = Column(DateTime, default=datetime.utcnow)

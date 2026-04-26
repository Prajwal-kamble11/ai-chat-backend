import uuid
from datetime import datetime
from sqlalchemy.sql import func

from sqlalchemy import Column, String, ForeignKey, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.db import Base


# 🔹 USER TABLE
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    plan = Column(String, default="free")
    subscription_expires_at = Column(DateTime, nullable=True)

    # ✅ Relationship (1 user → many chats)
    chats = relationship("Chat", back_populates="user", cascade="all, delete")
    files = relationship("File", back_populates="user", cascade="all, delete")


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

# 🔹 FILE TABLE (For RAG)
class File(Base):
    __tablename__ = "files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="files")
    chunks = relationship("DocumentChunk", back_populates="file", cascade="all, delete")

# 🔹 DOCUMENT CHUNKS TABLE (For Vector Search)
class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id = Column(UUID(as_uuid=True), ForeignKey("files.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(String, nullable=False)
    # Using 384 dimensions for all-MiniLM-L6-v2 embeddings
    embedding = Column(Vector(384), nullable=False)
    extra_metadata = Column(String, nullable=True) # JSON-like info (page number, etc.)

    # Relationships
    file = relationship("File", back_populates="chunks")

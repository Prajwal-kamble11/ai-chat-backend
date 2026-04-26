# AMI - AI-Powered Assistant with Knowledge Base

## 1. Project Overview
AMI is a high-performance AI chatbot platform. It features a custom **JWT-based Authentication** system, **Usage Quotas**, and a sophisticated **RAG (Retrieval-Augmented Generation)** pipeline that allows users to upload documents and chat with them.

### **Core Features**
- **Sharp Memory (RAG)**: Upload PDF/TXT files. The system automatically chunks and indexes them using `pgvector` and local embeddings (`all-MiniLM-L6-v2`).
- **Hybrid Search**: Combines semantic vector search with keyword-based full-text search using Reciprocal Rank Fusion (RRF) for maximum accuracy.
- **Custom Auth**: Secure Login/Signup with `bcrypt` password hashing and JWT session management.
- **Background Processing**: Heavy tasks like file indexing and chat summarization are handled asynchronously via **Arq**.
- **Usage Limits**: Tiered quota system (Free vs Pro) to manage API costs.

### **Tech Stack**
- **Backend**: FastAPI, SQLAlchemy 2.0 (Async), PostgreSQL + `pgvector`.
- **Frontend**: React (Vite), Tailwind CSS, Framer Motion, Lucide Icons.
- **AI Engine**: Groq (LLaMA 3.1) for chat, Hugging Face (Sentence Transformers) for local embeddings.
- **Task Queue**: Redis + Arq.

---

## 2. Getting Started

### **Environment Setup**
Create a `.env` file in the `ai-chat-backend` directory:
```env
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
GROQ_API_KEY=your_groq_key
REDIS_URL=redis://localhost:6379
SECRET_KEY=your_jwt_secret
HUGGINGFACE_TOKEN=optional_token
FRONTEND_URL=http://localhost:5173
```

### **Running the Application**
1. **Backend Server**:
   ```bash
   uv run uvicorn app.main:app --reload
   ```
2. **Background Worker**:
   ```bash
   uv run arq app.worker.WorkerSettings
   ```
3. **Frontend**:
   ```bash
   npm run dev
   ```

---

## 3. Architecture Details

### **RAG Pipeline**
1. **Upload**: User sends a PDF/TXT to `/files/upload`.
2. **Queue**: The file is sent to an Arq task.
3. **Index**: The worker extracts text, chunks it recursively, generates 384-dimension embeddings, and stores them in the `document_chunks` table.
4. **Retrieve**: When chatting, the system performs a hybrid search to find the most relevant context and injects it into the AI's prompt.

### **Database Schema**
- `users`: Auth, Plan (Free/Pro/Premium).
- `chats`: Conversation metadata.
- `messages`: Chat history.
- `files`: Uploaded document metadata.
- `document_chunks`: Chunks of text with their corresponding vector embeddings.

---

## 4. Maintenance
- **Migrations**: Use `alembic upgrade head` to apply schema changes.
- **Cleanup**: Unused debugging scripts and old Clerk-related logic have been removed for a clean, production-ready codebase.
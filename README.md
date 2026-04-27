# 🤖 AMI AI - Advanced RAG Chat Backend

A high-performance, asynchronous AI Chat backend built with **FastAPI**, **pgvector**, and **Groq**. This system features a full Retrieval-Augmented Generation (RAG) pipeline, allowing users to chat with their own documents (PDF/TXT) using state-of-the-art LLMs.

---

## 🚀 Features

- **Hybrid RAG Pipeline**: Combines semantic vector search (pgvector) with keyword-based retrieval for highly accurate context injection.
- **Asynchronous Processing**: Uses **Arq** and **Redis** to handle heavy document indexing and summarization tasks in the background.
- **Server-Sent Events (SSE)**: Real-time, streaming AI responses for a smooth "typing" experience.
- **Custom JWT Authentication**: Secure user registration and login with encrypted password hashing (Bcrypt).
- **Advanced Memory**: Implements a "Summary-First" memory system to maintain long-term context without hitting token limits.
- **Memory-Efficient Embeddings**: Leverages the **Hugging Face Inference API** to maintain a tiny footprint (under 100MB RAM), perfect for free-tier deployments.

---

## 🛠 Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **AI Model**: [Groq](https://groq.com/) (LLaMA 3.1 70B)
- **Database**: [PostgreSQL](https://www.postgresql.org/) with [pgvector](https://github.com/pgvector/pgvector)
- **Embeddings**: [Hugging Face Inference API](https://huggingface.co/docs/api-inference/index)
- **Task Queue**: [Arq](https://github.com/samuelcolvin/arq) + [Redis](https://redis.io/)
- **ORM**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/)

---

## ⚙️ Installation & Setup

### 1. Prerequisites
- Python 3.12+
- PostgreSQL (with pgvector extension)
- Redis

### 2. Clone and Install
```bash
git clone https://github.com/your-username/ai-chat-backend.git
cd ai-chat-backend
pip install uv
uv sync
```

### 3. Environment Configuration
Create a `.env` file in the root directory:
```env
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
GROQ_API_KEY=your_groq_key
HUGGINGFACE_TOKEN=your_hf_token
HF_API_URL=https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2/pipeline/feature-extraction
REDIS_URL=redis://localhost:6379
SECRET_KEY=your_jwt_secret
ALGORITHM=HS256
FRONTEND_URL=http://localhost:5173
```

---

## 🛫 Deployment (Render)

1. **Build Command**: `pip install uv && uv sync`
2. **Start Command (API)**: `uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. **Start Command (Worker)**: `uv run arq app.worker.WorkerSettings`

---

## 📄 License
This project is licensed under the MIT License.
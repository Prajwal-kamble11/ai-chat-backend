from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.vector_service import get_embeddings
from app.models import DocumentChunk

async def search_relevant_context(query: str, user_id: str, db: AsyncSession, limit: int = 5) -> str:
    """
    Performs Hybrid Search (Vector + Full-Text) on DocumentChunks.
    Uses Reciprocal Rank Fusion (RRF) logic simplified for SQL.
    """
    
    query_embedding = get_embeddings(query)
    
    # SQL for Hybrid Search using pgvector and Postgres Full-Text Search
    # We combine semantic similarity and keyword matching
    hybrid_search_query = text("""
        WITH vector_search AS (
            SELECT id, 1.0 / (ROW_NUMBER() OVER (ORDER BY embedding <=> :embedding) + 60) as score
            FROM document_chunks
            WHERE user_id = :user_id
            ORDER BY embedding <=> :embedding
            LIMIT 20
        ),
        keyword_search AS (
            SELECT id, 1.0 / (ROW_NUMBER() OVER (ORDER BY ts_rank(to_tsvector('english', content), plainto_tsquery('english', :query)) DESC) + 60) as score
            FROM document_chunks
            WHERE user_id = :user_id 
              AND to_tsvector('english', content) @@ plainto_tsquery('english', :query)
            ORDER BY ts_rank(to_tsvector('english', content), plainto_tsquery('english', :query)) DESC
            LIMIT 20
        )
        SELECT dc.content, 
               COALESCE(vs.score, 0) + COALESCE(ks.score, 0) as combined_score
        FROM document_chunks dc
        LEFT JOIN vector_search vs ON dc.id = vs.id
        LEFT JOIN keyword_search ks ON dc.id = ks.id
        WHERE vs.id IS NOT NULL OR ks.id IS NOT NULL
        ORDER BY combined_score DESC
        LIMIT :limit;
    """)
    
    result = await db.execute(hybrid_search_query, {
        "embedding": str(query_embedding),
        "query": query,
        "user_id": user_id,
        "limit": limit
    })
    
    chunks = result.all()
    
    if not chunks:
        return ""
    
    # Combine retrieved chunks into a single context string
    context = "\n---\n".join([c[0] for c in chunks])
    return context

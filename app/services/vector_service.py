from sentence_transformers import SentenceTransformer
import numpy as np
from app.core.config import settings
from huggingface_hub import login
import os

# If a token is provided, log in to Hugging Face
if settings.HUGGINGFACE_TOKEN:
    try:
        login(token=settings.HUGGINGFACE_TOKEN)
        print("✅ Logged into Hugging Face Hub")
    except Exception as e:
        print(f"⚠️ Failed to log into Hugging Face: {e}")

# Load the model once at startup
# This model has 384 dimensions
# We use the specific name requested by the user
model_name = 'sentence-transformers/all-MiniLM-L6-v2'
model = SentenceTransformer(model_name)

def get_embeddings(text: str):
    """
    Generate vector embeddings for a given text.
    """
    embedding = model.encode(text)
    return embedding.tolist()

def get_batch_embeddings(texts: list[str]):
    """
    Generate embeddings for multiple texts at once.
    """
    embeddings = model.encode(texts)
    return embeddings.tolist()

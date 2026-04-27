import httpx
import time
from app.core.config import settings

def get_headers():
    """
    Returns the headers for the Hugging Face API.
    Only includes the Authorization header if the token is present.
    """
    headers = {}
    if settings.HUGGINGFACE_TOKEN:
        headers["Authorization"] = f"Bearer {settings.HUGGINGFACE_TOKEN}"
    return headers

def get_embeddings(text: str, retries: int = 5):
    """
    Generate vector embeddings using Hugging Face Inference API.
    Retries up to 5 times if the model is still loading.
    """
    if not settings.HUGGINGFACE_TOKEN:
        print("⚠️ HUGGINGFACE_TOKEN is missing! Embeddings might fail or be throttled.")
    
    payload = {"inputs": text, "options": {"wait_for_model": True}}
    
    with httpx.Client() as client:
        # We use a slightly more robust URL pattern
        api_url = settings.HF_API_URL
        print(f"DEBUG: Calling HF API -> {api_url}")
        response = client.post(api_url, headers=get_headers(), json=payload, timeout=30.0)
        
        if response.status_code != 200:
            # Handle potential model loading delay
            if response.status_code == 503 or "loading" in response.text:
                if retries > 0:
                    print(f"⏳ Model is loading... Retrying ({5 - retries + 1}/5)")
                    time.sleep(10)
                    return get_embeddings(text, retries - 1)
            
            raise Exception(f"HF API Error (Status {response.status_code}): {response.text}")
            
        return response.json()

def get_batch_embeddings(texts: list[str], retries: int = 5):
    """
    Generate embeddings for multiple texts at once using the API.
    Retries up to 5 times if the model is still loading.
    """
    if not settings.HUGGINGFACE_TOKEN:
        print("⚠️ HUGGINGFACE_TOKEN is missing!")

    payload = {"inputs": texts, "options": {"wait_for_model": True}}
    
    with httpx.Client() as client:
        api_url = settings.HF_API_URL
        response = client.post(api_url, headers=get_headers(), json=payload, timeout=60.0)
        
        if response.status_code != 200:
            # Handle potential model loading delay
            if response.status_code == 503 or "loading" in response.text:
                if retries > 0:
                    print(f"⏳ Model is loading... Retrying ({5 - retries + 1}/5)")
                    time.sleep(12)
                    return get_batch_embeddings(texts, retries - 1)
            
            raise Exception(f"HF API Error (Status {response.status_code}): {response.text}")
            
        return response.json()

import urllib.request
import json
from jose import jwt

from app.core.config import settings

# Cache for JWKS keys to prevent hitting the network on every request
_jwks_cache = None

def get_jwks():
    global _jwks_cache
    if not _jwks_cache and settings.CLERK_JWKS_URL:
        try:
            req = urllib.request.Request(settings.CLERK_JWKS_URL, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(req, timeout=10)
            _jwks_cache = json.loads(response.read())
        except Exception as e:
            print(f"Failed to fetch JWKS: {e}")
    return _jwks_cache

# 🔐 Decode token (Secure Clerk JWT validation)
def decode_clerk_token(token: str):
    try:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        if not kid:
            return None
        
        jwks = get_jwks()
        rsa_key = next((key for key in jwks.get("keys", []) if key["kid"] == kid), None) if jwks else None
        
        # If the key ID isn't in cache, it might have been rotated by Clerk. Refetch!
        if not rsa_key and settings.CLERK_JWKS_URL:
            global _jwks_cache
            _jwks_cache = None
            jwks = get_jwks()
            rsa_key = next((key for key in jwks.get("keys", []) if key["kid"] == kid), None) if jwks else None

        if not rsa_key:
            print(f"Token decode error: Could not find matching public key for kid {kid}")
            return None

        # Fully secure decode checking signature and expiry
        return jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_aud": False  # Aud validation can be added if frontend strictly limits audiences
            }
        )
    except Exception as e:
        print(f"Token decode error: {e}")
        return None
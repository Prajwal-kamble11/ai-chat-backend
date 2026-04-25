from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # Groq AI
    GROQ_API_KEY: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Clerk Authentication
    CLERK_SECRET_KEY: str = ""
    CLERK_JWKS_URL: str = ""

    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""

    # Frontend URL (for CORS)
    FRONTEND_URL: str = "http://localhost:5173"


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# ✅ Single global instance — import this everywhere
settings = Settings()

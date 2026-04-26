from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import traceback

from fastapi.middleware.cors import CORSMiddleware
from app.db import engine
from app.routes.user import router as user_router
from app.routes.chat import router as chat_router
from app.routes.payment import router as payment_router
from app.routes.auth import router as auth_router
from app.routes.files import router as files_router
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.redis import redis_client, init_arq

from fastapi_limiter import FastAPILimiter

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Step 1: startup")
    async with engine.begin():
        print("Step 2: connected to postgres")
        
    await FastAPILimiter.init(redis_client)
    print("Step 4: FastAPILimiter initialized")
    
    await init_arq()
    print("Step 5: Arq pool initialized")
    
    yield


app = FastAPI(lifespan=lifespan)

# ✅ Add CORS middleware (Permissive for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": True, "message": str(exc.detail), "code": exc.status_code},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "message": "Invalid request parameters",
            "details": exc.errors(),
            "code": 422
        },
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"error": True, "message": "Internal server error", "code": 500},
    )


@app.get("/")
def root():
    return {"message": "Backend running 🚀"}


app.include_router(user_router)
app.include_router(chat_router)
app.include_router(payment_router)
app.include_router(auth_router)
app.include_router(files_router)
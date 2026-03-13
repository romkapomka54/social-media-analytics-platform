"""
FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .routers import youtube


from .core.config import settings
from .routers import health, chat, approval


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print(f"🚀 Starting {settings.project_name}...")
    print(f"📊 Supabase URL: {settings.supabase_url[:30]}...")
    
    # Test Supabase connection
    try:
        client = settings.supabase_client
        result = client.table("tenants").select("count", count="exact").execute()
        print(f"✅ Supabase connected successfully!")
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
    
    yield
    
    # Shutdown
    print("👋 Shutting down...")


# Create FastAPI app
app = FastAPI(
    title=settings.project_name,
    description="API for Social Media Analytics Platform with AI-powered comment analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix=settings.api_v1_prefix)
app.include_router(chat.router, prefix=settings.api_v1_prefix)
app.include_router(approval.router, prefix=settings.api_v1_prefix)
app.include_router(youtube.router, prefix=settings.api_v1_prefix)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.project_name}",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Health check (alias for /api/v1/health)."""
    return {"status": "ok"}

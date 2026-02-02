from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import (
    chat_router,
    tools_router,
    business_profile_router,
    dashboard_router,
    community_router,
)
from .core.tool_registry import ToolRegistry
from .core.cache import get_cache
from .core.logging import setup_logging, get_logger
from .tools.market_research import MarketResearchTool
from .tools.social_media_coach import SocialMediaCoachTool
from .tools.review_responder import ReviewResponderTool
from .tools.business_advisor import BusinessAdvisorTool

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    setup_logging()
    logger.info("Starting PHOW API")

    # Startup: Register tools
    ToolRegistry.register(MarketResearchTool())
    ToolRegistry.register(SocialMediaCoachTool())
    ToolRegistry.register(ReviewResponderTool())
    ToolRegistry.register(BusinessAdvisorTool())
    logger.info("Registered tools", tools=ToolRegistry.list_tools())

    yield

    # Shutdown: Close Redis connection
    logger.info("Shutting down PHOW API")
    cache = get_cache()
    await cache.close()
    logger.info("Closed Redis connection")


# Create FastAPI app
app = FastAPI(
    title="PHOW API",
    description="AI-powered analytics platform for small business owners",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",  # Alternative port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router, prefix="/api")
app.include_router(tools_router, prefix="/api")
app.include_router(business_profile_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(community_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "message": "PHOW API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    cache = get_cache()
    redis_status = "ok" if await cache.health_check() else "unavailable"

    return {
        "status": "healthy",
        "services": {
            "api": "ok",
            "redis": redis_status,
        },
    }

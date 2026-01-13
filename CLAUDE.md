# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PHOW is an AI-powered analytics platform for small business owners. The MVP features a Location Scout tool using Google Maps and LLM analysis with a scalable, production-ready architecture.

## Architecture

### Stack
- **Frontend**: Next.js 15 with App Router, TypeScript, Tailwind CSS, shadcn/ui
- **Backend**: Python FastAPI with layered architecture (Repository → Service → API)
- **Database**: Supabase (PostgreSQL)
- **Caching**: Redis for external API response caching
- **Background Jobs**: Celery with Redis broker
- **LLM Framework**: LangChain with OpenAI and Anthropic support
- **External APIs**: Google Maps (Places, Geocoding)

### Architecture Patterns
- **Repository Pattern**: Database operations abstracted in `repositories/`
- **Service Layer**: Business logic in `services/`
- **Dependency Injection**: FastAPI Depends() for clean separation
- **Caching Decorator**: `@cached()` for automatic Redis caching
- **Retry Logic**: Tenacity for API resilience

## Development Commands

### Frontend (from `frontend/`)
```bash
npm run dev          # Start dev server on port 3000
npm run build        # Build for production
npm run lint         # Run ESLint
```

### Backend (from `backend/`)
```bash
pip install -r requirements.txt              # Install dependencies
uvicorn app.main:app --reload --port 8000    # Start FastAPI server

# Celery worker (for background tasks)
celery -A app.workers.celery_app worker --loglevel=info
```

### Docker (from root)
```bash
docker-compose up           # Start all services (API, DB, Redis, Celery)
docker-compose up backend   # Start only specific service
```

## Key File Locations

### Backend Core
- `backend/app/main.py` - FastAPI app with lifespan events
- `backend/app/core/llm.py` - LangChain LLM service (OpenAI/Anthropic)
- `backend/app/core/cache.py` - Redis cache manager with decorator
- `backend/app/core/tool_registry.py` - Tool registration system
- `backend/app/core/config.py` - Centralized configuration

### Backend Layers
- `backend/app/repositories/` - Database access layer
  - `conversation_repository.py` - Conversation CRUD operations
  - `message_repository.py` - Message CRUD operations
- `backend/app/services/` - Business logic layer
  - `chat_service.py` - Chat orchestration
  - `location_service.py` - Location analysis with caching
- `backend/app/api/routes/` - HTTP endpoints
  - `chat.py` - SSE streaming chat endpoint
  - `tools.py` - Tool management endpoints
- `backend/app/api/deps.py` - Dependency injection providers

### Tools & Workers
- `backend/app/tools/base.py` - Base tool interface
- `backend/app/tools/location_scout/` - Location Scout implementation
- `backend/app/workers/celery_app.py` - Celery configuration
- `backend/app/workers/tasks.py` - Background tasks (batch analysis, reports)

### Frontend
- `frontend/src/app/page.tsx` - Main page with chat interface
- `frontend/src/components/chat/` - Chat UI components
- `frontend/src/lib/api.ts` - Backend API client with SSE
- `frontend/src/lib/session.ts` - Anonymous session management

## Adding New Tools

1. Create tool directory: `backend/app/tools/your_tool/`
2. Implement tool class extending `BaseTool`:
   ```python
   from ..base import BaseTool, ToolContext, ToolResponse
   from ...core.llm import get_llm_service
   from ...services.your_service import YourService

   class YourTool(BaseTool):
       tool_id = "your_tool"
       name = "Your Tool"
       description = "Tool description"
       icon = "🔧"

       def __init__(self):
           self.service = YourService()
           self.llm = get_llm_service()

       async def process_stream(self, query: str, context: ToolContext):
           # Implementation with LangChain
           ...
   ```
3. Create service in `backend/app/services/your_service.py` with business logic
4. Register in `backend/app/main.py` lifespan:
   ```python
   ToolRegistry.register(YourTool())
   ```

## Using Caching

Decorate service methods with `@cached()`:
```python
from ...core.cache import cached

@cached(ttl=3600, key_prefix="geocode")
async def geocode_address(self, address: str):
    # Results cached for 1 hour
    return await self.maps_client.geocode(address)
```

## Background Tasks

Use Celery for long-running operations:
```python
from app.workers import analyze_location_batch

# Async task
result = analyze_location_batch.delay(addresses, business_type)
result_data = result.get()  # Blocks until complete
```

## Environment Variables

Copy `.env.example` in `backend/` and configure:
- **Supabase**: URL and service key
- **LLMs**: OpenAI and/or Anthropic API keys
- **Google Maps**: API key for Places/Geocoding
- **Redis**: URL for caching (default: localhost:6379)
- **Celery**: Broker and result backend URLs

## Database

Migrations: `supabase/migrations/`

Schema:
- `conversations` - Session-based chats (supports future user_id)
- `messages` - Chat messages with JSONB metadata

## Testing

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

## Deployment Notes

- FastAPI: Deploy on Railway/Render/Fly.io
- Redis: Use managed Redis (Upstash, Redis Cloud)
- Celery: Run as separate dyno/service
- Frontend: Vercel/Netlify
- Database: Supabase hosted

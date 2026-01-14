# Backend CLAUDE.md

This file provides detailed guidance for working with the PHOW backend codebase. See the root `CLAUDE.md` for project-wide principles and architecture overview.

## Backend Architecture

### Stack & Dependencies
- **Framework**: FastAPI 0.109+ with async/await throughout
- **Database**: Supabase (PostgreSQL) via `supabase-py` client
- **Caching**: Redis 5.0+ with async support (`redis.asyncio`)
- **Background Jobs**: Celery 5.3+ with Redis broker
- **LLM Framework**: LangChain 0.1+ with LangGraph for agent orchestration
- **LLM Providers**: OpenAI and Anthropic (configurable via `llm_provider` setting)
- **Streaming**: SSE (Server-Sent Events) via `sse-starlette`
- **Logging**: Structlog for structured logging
- **Retry Logic**: Tenacity for resilient API calls
- **Code Formatting**: Black 24.0+

### Directory Structure

```
backend/app/
├── main.py                    # FastAPI app, lifespan events, tool registration
├── api/                       # HTTP layer
│   ├── deps.py                # Dependency injection (Supabase, services, cache)
│   └── routes/                # API endpoints
│       ├── chat.py            # SSE streaming chat endpoint
│       └── tools.py           # Tool management endpoints
├── core/                      # Core infrastructure
│   ├── config.py              # Pydantic settings (env vars)
│   ├── cache.py               # Redis cache manager + @cached decorator
│   ├── llm.py                 # LangChain LLM service factory
│   ├── logging.py             # Structlog setup
│   └── tool_registry.py       # Tool registration system
├── models/                    # Pydantic models
│   └── chat.py                # Request/response models
├── repositories/              # Database access layer
│   ├── base.py                # BaseRepository abstract class
│   ├── conversation_repository.py
│   ├── message_repository.py
│   ├── business_profile_repository.py
│   ├── llm_response_repository.py
│   └── tool_activity_repository.py
├── services/                  # Business logic layer
│   ├── chat_service.py        # Chat orchestration, message processing
│   ├── tracking_service.py    # LLM/tool activity tracking
│   └── business_profile_service.py
├── tools/                     # Tool implementations
│   ├── base.py                # BaseTool abstract class
│   ├── location_scout/        # Location analysis tool
│   │   ├── tool.py            # Tool wrapper
│   │   ├── agent.py           # LangGraph agent
│   │   ├── agent_tools.py     # LangChain tools (Google Maps)
│   │   └── google_maps.py     # Google Maps API client
│   ├── market_validator/      # Market validation tool
│   │   ├── tool.py
│   │   ├── agent.py
│   │   ├── agent_tools.py
│   │   ├── prompts.py
│   │   └── census_client.py
│   └── competitor_analyzer/   # Competitor analysis tool
│       ├── tool.py
│       ├── agent.py
│       ├── agent_tools.py
│       ├── prompts.py
│       └── yelp_client.py
└── workers/                   # Background tasks
    ├── celery_app.py          # Celery configuration
    └── tasks.py               # Celery task definitions
```

## Core Patterns

### 1. Repository Pattern
All database operations go through repositories that extend `BaseRepository`:
```python
from ..repositories.base import BaseRepository
from supabase import Client

class YourRepository(BaseRepository):
    def __init__(self, db: Client):
        super().__init__(db)
    
    async def create(self, **kwargs) -> dict:
        result = self.db.table("your_table").insert(kwargs).execute()
        return result.data[0]
```

**Key Repositories:**
- `ConversationRepository`: CRUD for conversations
- `MessageRepository`: CRUD for messages, history retrieval
- `BusinessProfileRepository`: Business profile management
- `LLMResponseRepository`: LLM response tracking
- `ToolActivityRepository`: Tool usage tracking

### 2. Service Layer
Services contain business logic and orchestrate repositories:
```python
from ..repositories import YourRepository
from supabase import Client

class YourService:
    def __init__(self, db: Client):
        self.repo = YourRepository(db)
    
    async def do_something(self, param: str):
        # Business logic here
        return await self.repo.create(...)
```

**Key Services:**
- `ChatService`: Message processing, conversation management, tool invocation
- `TrackingService`: LLM calls, tool activities, performance metrics
- `BusinessProfileService`: Business profile operations

### 3. Dependency Injection
Use FastAPI `Depends()` for clean dependency management:
```python
# In api/deps.py
def get_your_service(db: Client = Depends(get_supabase)) -> YourService:
    return YourService(db)

# In routes
@router.post("/endpoint")
async def endpoint(service: YourService = Depends(get_your_service)):
    return await service.do_something()
```

**Available Dependencies:**
- `get_supabase()`: Supabase client (singleton)
- `get_chat_service()`: ChatService instance
- `get_tracking_service()`: TrackingService instance
- `get_cache_manager()`: CacheManager instance

### 4. Tool System
Tools extend `BaseTool` and implement:
- `process()`: Non-streaming response
- `process_stream()`: Streaming response (async generator)
- `get_system_prompt()`: LLM system prompt

```python
from ..base import BaseTool, ToolContext, ToolResponse

class YourTool(BaseTool):
    tool_id = "your_tool"
    name = "Your Tool"
    description = "Tool description"
    icon = "🔧"
    hints = ["Example query 1", "Example query 2"]
    capabilities = ["Feature 1", "Feature 2"]
    
    async def process_stream(self, query: str, context: ToolContext):
        # Stream response chunks
        yield "chunk 1"
        yield "chunk 2"
```

**Tool Registration:**
Tools are registered in `main.py` lifespan:
```python
from .tools.your_tool import YourTool
ToolRegistry.register(YourTool())
```

### 5. Caching Pattern
Use `@cached()` decorator for automatic Redis caching:
```python
from ...core.cache import cached

@cached(ttl=3600, key_prefix="geocode")
async def geocode_address(self, address: str):
    # Results cached for 1 hour
    return await self.maps_client.geocode(address)
```

Cache keys are auto-generated from function name, args, and kwargs.

### 6. Streaming Responses
Chat endpoint uses SSE for streaming:
```python
from sse_starlette.sse import EventSourceResponse

async def generate():
    async for chunk in service.process_stream(...):
        yield {"event": "chunk", "data": json.dumps({"content": chunk})}
    yield {"event": "done", "data": json.dumps({"conversation_id": id})}

return EventSourceResponse(generate())
```

Events: `chunk`, `done`, `error`

## Database Schema

### Tables
- **conversations**: Session-based chats (supports future `user_id`)
  - `id` (UUID), `session_id` (TEXT), `tool_id` (TEXT), `title` (TEXT), timestamps
- **messages**: Chat messages with JSONB metadata
  - `id` (UUID), `conversation_id` (UUID FK), `role` (TEXT), `content` (TEXT), `metadata` (JSONB)
- **business_profiles**: Business profile data
- **llm_responses**: LLM call tracking
- **tool_activities**: Tool usage tracking

### Indexes
- `idx_conversations_session` on `conversations(session_id)`
- `idx_messages_conversation` on `messages(conversation_id)`

## Configuration

### Environment Variables
All config via `app/core/config.py` using Pydantic Settings:
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_SERVICE_KEY`: Supabase service role key
- `OPENAI_API_KEY`: OpenAI API key
- `ANTHROPIC_API_KEY`: Anthropic API key
- `LLM_PROVIDER`: "openai" or "anthropic" (default: "anthropic")
- `GOOGLE_MAPS_API_KEY`: Google Maps API key
- `REDIS_URL`: Redis connection URL (default: "redis://localhost:6379/0")
- `CACHE_TTL`: Default cache TTL in seconds (default: 3600)
- `CELERY_BROKER_URL`: Celery broker URL
- `CELERY_RESULT_BACKEND`: Celery result backend URL
- `DEBUG`: Enable debug mode
- `ENVIRONMENT`: "development" or "production"

Access via: `from ..core.config import get_settings; settings = get_settings()`

## LLM Integration

### LLM Service
Located in `app/core/llm.py`:
```python
from ..core.llm import get_llm_service

llm = get_llm_service()  # Returns LangChain LLM (OpenAI or Anthropic)
```

### LangChain Patterns
- Use LangChain tools for external API calls
- Use LangGraph for agent orchestration
- Tools should be registered with tracking via `ToolContext.tracking_service`

## Logging

Structured logging via Structlog:
```python
from ..core.logging import get_logger

logger = get_logger("module_name")
logger.info("Message", key=value, another_key=another_value)
logger.error("Error", error=str(e), error_type=type(e).__name__)
```

## Error Handling

- Use try/except blocks for error handling
- Log errors with context
- Return user-friendly error messages in API responses
- Track errors in `tool_activities` table via `TrackingService.fail_tool_activity()`

## Testing

Run tests with pytest:
```bash
cd backend
pytest
```

## Code Style

- **Formatting**: Use Black (`black app/`)
- **Type Hints**: Use type hints for all function parameters and returns
- **Async**: All I/O operations should be async
- **Imports**: Use absolute imports from `app.` root
- **Naming**: 
  - Classes: PascalCase
  - Functions/methods: snake_case
  - Constants: UPPER_SNAKE_CASE

## Common Tasks

### Adding a New Tool
1. Create directory: `app/tools/your_tool/`
2. Implement `tool.py` extending `BaseTool`
3. Create `agent.py` with LangGraph agent (if needed)
4. Create `agent_tools.py` with LangChain tools
5. Register in `main.py` lifespan: `ToolRegistry.register(YourTool())`

### Adding a New Repository
1. Create `app/repositories/your_repository.py`
2. Extend `BaseRepository`
3. Implement CRUD methods using Supabase client
4. Add to `app/repositories/__init__.py` exports

### Adding a New Service
1. Create `app/services/your_service.py`
2. Inject repositories via constructor
3. Implement business logic methods
4. Add dependency in `app/api/deps.py`
5. Use in routes via `Depends()`

### Adding a New API Route
1. Create route in `app/api/routes/your_route.py`
2. Use `APIRouter` with prefix
3. Inject services via `Depends()`
4. Register in `main.py`: `app.include_router(your_router, prefix="/api")`

## Key Files Reference

- **Entry Point**: `app/main.py` - FastAPI app, lifespan, CORS, routers
- **Chat Endpoint**: `app/api/routes/chat.py` - SSE streaming chat
- **Chat Service**: `app/services/chat_service.py` - Message processing orchestration
- **Tool Base**: `app/tools/base.py` - BaseTool interface
- **Tool Registry**: `app/core/tool_registry.py` - Tool management
- **Cache**: `app/core/cache.py` - Redis caching with decorator
- **Config**: `app/core/config.py` - Environment configuration
- **LLM**: `app/core/llm.py` - LangChain LLM factory

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run dev server
uvicorn app.main:app --reload --port 8000

# Format code
black app/

# Run Celery worker
celery -A app.workers.celery_app worker --loglevel=info

# Check health
curl http://localhost:8000/health
```

## Important Notes

- **All database operations are async** - Use `await` for all Supabase calls
- **Use repositories, not direct Supabase calls** - Maintains abstraction
- **Cache external API calls** - Use `@cached()` decorator
- **Track tool activities** - Use `TrackingService` in tool context
- **Stream responses** - Use async generators for streaming
- **Handle errors gracefully** - Log and return user-friendly messages
- **Follow existing patterns** - Match code style and structure of similar files

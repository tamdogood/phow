# PHOW Backend

Production-ready FastAPI backend with layered architecture for AI-powered business analytics.

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│              API Layer (FastAPI)                │
│  ├── chat.py (SSE streaming)                    │
│  └── tools.py (tool management)                 │
└─────────────────────────────────────────────────┘
                    ↓ Depends()
┌─────────────────────────────────────────────────┐
│              Service Layer                      │
│  ├── ChatService (orchestration)                │
│  └── LocationService (caching + retry)          │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│           Repository Layer                      │
│  ├── ConversationRepository (DB ops)            │
│  └── MessageRepository (DB ops)                 │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│         Infrastructure Layer                    │
│  ├── Supabase (PostgreSQL)                      │
│  ├── Redis (caching)                            │
│  ├── LangChain (LLM orchestration)              │
│  └── Celery (background tasks)                  │
└─────────────────────────────────────────────────┘
```

## Key Features

### 🏗️ Layered Architecture
- **Repositories**: Database operations (CRUD)
- **Services**: Business logic with caching
- **APIs**: HTTP endpoints with dependency injection
- **Workers**: Background tasks via Celery

### 🚀 Performance
- **Redis Caching**: Google Maps API responses cached (saves $$ and latency)
- **Retry Logic**: Automatic retries with exponential backoff
- **Async Everything**: Full async/await support
- **Connection Pooling**: Efficient resource usage

### 🤖 LLM Integration
- **LangChain**: Unified interface for OpenAI/Anthropic
- **Streaming**: Real-time SSE response streaming
- **Prompt Management**: Structured prompts via templates

### 📦 Extensibility
- **Tool Registry**: Easy plugin system for new tools
- **Service Layer**: Add services without touching APIs
- **Background Jobs**: Celery tasks for heavy operations

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Run Services
```bash
# Terminal 1: FastAPI server
uvicorn app.main:app --reload --port 8000

# Terminal 2: Celery worker (optional, for background tasks)
celery -A app.workers.celery_app worker --loglevel=info

# Terminal 3: Redis (if not using Docker)
redis-server
```

### Or Use Docker
```bash
cd ..
docker-compose up
```

## Project Structure

```
app/
├── core/                   # Core infrastructure
│   ├── config.py          # Settings management
│   ├── llm.py             # LangChain service
│   ├── cache.py           # Redis caching
│   └── tool_registry.py   # Tool registration
├── repositories/          # Database layer
│   ├── conversation_repository.py
│   └── message_repository.py
├── services/              # Business logic
│   ├── chat_service.py
│   └── location_service.py
├── api/                   # HTTP layer
│   ├── routes/
│   │   ├── chat.py
│   │   └── tools.py
│   └── deps.py           # DI providers
├── tools/                # Extensible tools
│   ├── base.py
│   └── location_scout/
├── workers/              # Background tasks
│   ├── celery_app.py
│   └── tasks.py
└── main.py              # App entry point
```

## Adding a New Tool

1. **Create Tool Class** (`app/tools/your_tool/tool.py`):
```python
from ..base import BaseTool, ToolContext
from ...core.llm import get_llm_service
from ...services.your_service import YourService

class YourTool(BaseTool):
    tool_id = "your_tool"
    name = "Your Tool"
    description = "What it does"
    icon = "🔧"

    def __init__(self):
        self.service = YourService()
        self.llm = get_llm_service()

    async def process_stream(self, query: str, context: ToolContext):
        # Get data from service
        data = await self.service.get_data(query)

        # LLM analysis
        messages = [{"role": "user", "content": f"Analyze: {data}"}]
        async for chunk in self.llm.chat_stream(messages):
            yield chunk
```

2. **Create Service** (`app/services/your_service.py`):
```python
from ..core.cache import cached
from tenacity import retry, stop_after_attempt

class YourService:
    @cached(ttl=3600, key_prefix="your_data")
    @retry(stop=stop_after_attempt(3))
    async def get_data(self, query: str):
        # Business logic with caching + retry
        ...
```

3. **Register Tool** (in `app/main.py`):
```python
ToolRegistry.register(YourTool())
```

## Using Caching

```python
from app.core.cache import cached

@cached(ttl=3600, key_prefix="my_operation")
async def expensive_operation(param: str):
    # This result will be cached for 1 hour
    return await some_api_call(param)
```

## Background Tasks

```python
# Define task in app/workers/tasks.py
@celery_app.task
def long_running_task(param):
    # Heavy computation
    return result

# Use in code
from app.workers import long_running_task
result = long_running_task.delay(param)
```

## API Endpoints

- `POST /api/chat` - Streaming chat (SSE)
- `GET /api/chat/conversations?session_id=xxx` - List conversations
- `GET /api/chat/conversations/{id}/messages` - Get messages
- `GET /api/tools` - List available tools
- `GET /health` - Health check
- `GET /docs` - OpenAPI documentation

## Environment Variables

See `.env.example` for all configuration options:
- **Required**: LLM API keys, Google Maps API key, Supabase credentials
- **Optional**: Redis URL, Celery broker, cache TTL

## Testing

```bash
pytest
pytest --cov=app tests/
```

## Deployment

### Recommended Setup
- **API**: Railway/Render/Fly.io (FastAPI server)
- **Redis**: Upstash/Redis Cloud (managed)
- **Celery**: Separate dyno/service
- **Database**: Supabase (managed PostgreSQL)

### Environment Variables (Production)
- Set `ENVIRONMENT=production`
- Use managed Redis (not localhost)
- Update CORS origins in `main.py`
- Secure API keys via platform secrets

## License

MIT

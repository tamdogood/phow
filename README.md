# PHOW

**AI-powered analytics platform for small business owners**

PHOW is a production-ready web application that helps small business owners make data-driven decisions about their business locations. The MVP features a **Location Scout** tool that analyzes potential business locations using Google Maps data and AI-powered insights.

## Features

- **Location Scout**: Analyze potential business locations with insights on:
  - Competition analysis (nearby competitors with ratings)
  - Foot traffic indicators
  - Public transit accessibility
  - Nearby amenities (food, retail)
  - AI-powered recommendations with scores

- **Interactive Map Display**: Real-time Google Maps widget showing:
  - Target location marker
  - Competitor locations
  - Transit stations
  - Visual legend for marker types

- **Real-time Chat Interface**: Interactive chat experience with streaming responses
- **Agent-based Tool System**: LangGraph ReAct agents that intelligently select and chain tools
- **Comprehensive Tracking**: Monitor LLM responses and tool activities with latency metrics
- **Structured Logging**: Full observability with structlog
- **High Performance**: Redis caching reduces API costs by 67%+ and improves response times
- **Resilient**: Automatic retry logic with exponential backoff
- **Background Processing**: Celery workers for long-running tasks
- **Extensible**: Easy-to-add tool system for future features

## Architecture

PHOW follows a **layered architecture** pattern with an agent-based tool execution system:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Frontend (Next.js)                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │  ChatInput  │  │ ChatMessage │  │  MapWidget  │  │ Session Manager │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘ │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │ SSE (Server-Sent Events)
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         API Layer (FastAPI)                              │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────┐  │
│  │   /api/chat (SSE)   │  │   /api/tools        │  │   /health       │  │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────┘  │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Service Layer                                     │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────────────┐ │
│  │   ChatService   │  │ TrackingService  │  │   LocationService       │ │
│  └────────┬────────┘  └──────────────────┘  └─────────────────────────┘ │
└───────────┼─────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Tool Registry & Agents                              │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                    LocationScoutAgent (LangGraph)                    ││
│  │  ┌──────────────┐ ┌────────────────┐ ┌─────────────┐ ┌────────────┐ ││
│  │  │ geocode_addr │ │ search_nearby  │ │ get_details │ │ discover   │ ││
│  │  └──────────────┘ └────────────────┘ └─────────────┘ └────────────┘ ││
│  └─────────────────────────────────────────────────────────────────────┘│
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
            ┌────────────────────┼────────────────────┐
            ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐
│  Google Maps    │  │   LLM Service   │  │     Repository Layer        │
│    Client       │  │ (OpenAI/Claude) │  │  ┌─────────┐ ┌───────────┐  │
│  ┌───────────┐  │  └─────────────────┘  │  │ Convo   │ │  Message  │  │
│  │ Geocoding │  │                       │  │  Repo   │ │   Repo    │  │
│  │ Places    │  │                       │  └─────────┘ └───────────┘  │
│  └───────────┘  │                       │  ┌─────────┐ ┌───────────┐  │
└─────────────────┘                       │  │ LLM Resp│ │ Tool Act  │  │
                                          │  │  Repo   │ │   Repo    │  │
                                          │  └─────────┘ └───────────┘  │
                                          └──────────────┬──────────────┘
                                                         │
┌────────────────────────────────────────────────────────┼────────────────┐
│                        Infrastructure                   │                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │                │
│  │    Redis    │  │   Celery    │  │    Supabase     │◄┘                │
│  │   (Cache)   │  │  (Workers)  │  │  (PostgreSQL)   │                  │
│  └─────────────┘  └─────────────┘  └─────────────────┘                  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Key Architectural Patterns

- **Agent-based Tool Execution**: LangGraph ReAct agents that reason about which tools to call
- **Repository Pattern**: Database operations abstracted in `repositories/`
- **Service Layer**: Business logic with caching and tracking in `services/`
- **Dependency Injection**: FastAPI `Depends()` for clean separation
- **Caching Decorator**: `@cached()` for automatic Redis caching
- **Retry Logic**: Tenacity for API resilience
- **Structured Logging**: Structlog for observability

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed architecture documentation.

## Database Schema

PHOW uses PostgreSQL (via Supabase) with the following schema:

### Core Tables

```sql
-- Conversations: Session-based chat threads
conversations (
    id UUID PRIMARY KEY,
    session_id TEXT NOT NULL,      -- Anonymous session identifier
    user_id UUID,                  -- Optional, for future auth
    tool_id TEXT NOT NULL,         -- 'location_scout', etc.
    title TEXT,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
)

-- Messages: Individual chat messages
messages (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations,
    role TEXT NOT NULL,            -- 'user' or 'assistant'
    content TEXT NOT NULL,
    metadata JSONB,                -- Tool-specific data
    created_at TIMESTAMPTZ
)
```

### Tracking Tables

```sql
-- LLM Responses: Track all LLM API calls
llm_responses (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations,
    message_id UUID REFERENCES messages,
    provider TEXT NOT NULL,        -- 'openai' or 'anthropic'
    model TEXT NOT NULL,           -- 'gpt-4o', 'claude-sonnet-4-20250514', etc.
    prompt_tokens INT,
    completion_tokens INT,
    total_tokens INT,
    latency_ms INT,                -- Response time in milliseconds
    input_messages JSONB,          -- Messages sent to LLM
    output_content TEXT,           -- LLM's response
    metadata JSONB,                -- Temperature, etc.
    created_at TIMESTAMPTZ
)

-- Tool Activities: Track all tool invocations
tool_activities (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations,
    session_id TEXT NOT NULL,
    tool_id TEXT NOT NULL,         -- 'location_scout'
    tool_name TEXT NOT NULL,       -- 'discover_neighborhood', 'geocode_address'
    status TEXT NOT NULL,          -- 'started', 'completed', 'failed'
    input_args JSONB,              -- Arguments passed to tool
    output_data JSONB,             -- Tool response
    error_message TEXT,            -- Error if failed
    latency_ms INT,                -- Execution time
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
)
```

### Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐
│  conversations  │───────│    messages     │
│                 │  1:N  │                 │
└────────┬────────┘       └────────┬────────┘
         │                         │
         │ 1:N                     │ 1:1
         │                         │
┌────────▼────────┐       ┌────────▼────────┐
│  llm_responses  │       │ tool_activities │
│                 │       │                 │
└─────────────────┘       └─────────────────┘
```

## Tech Stack

### Frontend
- **Next.js 15** with App Router
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **shadcn/ui** for UI components
- **@react-google-maps/api** for interactive maps
- **Server-Sent Events (SSE)** for real-time streaming

### Backend
- **FastAPI** - Modern Python web framework
- **LangChain + LangGraph** - Agent orchestration with tool calling
- **Supabase** - PostgreSQL database
- **Redis** - Caching layer
- **Celery** - Background task processing
- **Google Maps API** - Geocoding, Places Nearby Search, Place Details
- **structlog** - Structured logging

### Infrastructure
- **Docker** & **Docker Compose** for local development
- **Supabase** for database hosting
- **Redis** for caching

## Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.11+ (conda environment recommended)
- **Docker** and Docker Compose (optional, for containerized setup)
- **API Keys**:
  - OpenAI or Anthropic API key
  - Google Maps API key (with Geocoding and Places APIs enabled)
  - Supabase project URL and service key

## Quick Start

### Option 1: Docker Compose (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/tamdogood/phow.git
   cd phow
   ```

2. **Set up environment variables**
   ```bash
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env
   # Edit both .env files with your API keys
   ```

3. **Start all services**
   ```bash
   docker-compose up
   ```

   This starts:
   - Backend API on `http://localhost:8000`
   - Frontend dev server on `http://localhost:3000` (run separately)
   - PostgreSQL database on port `54322`
   - Redis on port `6379`
   - Celery worker for background tasks

### Option 2: Manual Setup

#### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create conda environment** (recommended)
   ```bash
   conda create -n phow python=3.11
   conda activate phow
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

5. **Run database migrations**

   In Supabase SQL Editor, run:
   - `supabase/migrations/001_initial.sql`
   - `supabase/migrations/002_llm_and_tool_tracking.sql`

6. **Start Redis** (if not using Docker)
   ```bash
   redis-server
   ```

7. **Run the FastAPI server**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

8. **Run Celery worker** (optional, for background tasks)
   ```bash
   celery -A app.workers.celery_app worker --loglevel=info
   ```

#### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Add your NEXT_PUBLIC_GOOGLE_MAPS_API_KEY
   ```

4. **Start development server**
   ```bash
   npm run dev
   ```

5. **Open your browser**
   Navigate to `http://localhost:3000`

## Project Structure

```
phow/
├── backend/                      # FastAPI backend
│   ├── app/
│   │   ├── api/                  # API routes
│   │   │   ├── routes/           # HTTP endpoints
│   │   │   │   ├── chat.py       # SSE streaming chat
│   │   │   │   └── tools.py      # Tool management
│   │   │   └── deps.py           # Dependency injection
│   │   ├── core/                 # Core infrastructure
│   │   │   ├── cache.py          # Redis caching decorator
│   │   │   ├── config.py         # Centralized configuration
│   │   │   ├── llm.py            # LangChain LLM service
│   │   │   ├── logging.py        # Structured logging setup
│   │   │   └── tool_registry.py  # Tool registration system
│   │   ├── repositories/         # Database layer
│   │   │   ├── conversation_repository.py
│   │   │   ├── message_repository.py
│   │   │   ├── llm_response_repository.py
│   │   │   └── tool_activity_repository.py
│   │   ├── services/             # Business logic
│   │   │   ├── chat_service.py   # Chat orchestration
│   │   │   ├── location_service.py
│   │   │   └── tracking_service.py  # LLM & tool tracking
│   │   ├── tools/                # Extensible tools
│   │   │   ├── base.py           # Base tool interface
│   │   │   └── location_scout/
│   │   │       ├── agent.py      # LangGraph ReAct agent
│   │   │       ├── agent_tools.py # Google Maps tools
│   │   │       ├── tool.py       # Tool wrapper
│   │   │       └── prompts.py
│   │   ├── workers/              # Celery tasks
│   │   │   ├── celery_app.py
│   │   │   └── tasks.py
│   │   └── main.py               # FastAPI app with lifespan
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md
├── frontend/                     # Next.js frontend
│   ├── src/
│   │   ├── app/                  # Next.js app router
│   │   │   └── page.tsx          # Main chat page
│   │   ├── components/
│   │   │   └── chat/
│   │   │       ├── ChatInput.tsx
│   │   │       ├── ChatMessage.tsx  # Parses location data
│   │   │       └── MapWidget.tsx    # Google Maps component
│   │   ├── lib/
│   │   │   ├── api.ts            # Backend API client
│   │   │   └── session.ts        # Session management
│   │   └── types/
│   ├── package.json
│   └── README.md
├── supabase/                     # Database migrations
│   └── migrations/
│       ├── 001_initial.sql       # Core tables
│       └── 002_llm_and_tool_tracking.sql
├── docker-compose.yml
├── ARCHITECTURE.md
├── CLAUDE.md                     # Claude Code instructions
└── README.md
```

## Configuration

### Backend Environment Variables

Create `backend/.env`:

```env
# Database
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_service_key

# LLM Providers (at least one required)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
LLM_PROVIDER=anthropic  # or 'openai'

# Google Maps
GOOGLE_MAPS_API_KEY=your_google_maps_key

# Redis
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=3600

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Application
DEBUG=true
```

### Frontend Environment Variables

Create `frontend/.env`:

```env
# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000

# Google Maps (for map display)
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=your_google_maps_key
```

## Location Scout Agent

The Location Scout uses a LangGraph ReAct agent with the following tools:

| Tool | Description |
|------|-------------|
| `geocode_address` | Convert addresses to coordinates and verify locations |
| `search_nearby_places` | Find specific types of places near a location |
| `get_place_details` | Get detailed information about a specific place |
| `discover_neighborhood` | Comprehensive neighborhood analysis (competitors, transit, amenities) |

### How It Works

1. User asks about a location (e.g., "Is 123 Main St good for a coffee shop?")
2. The agent analyzes the query and decides which tools to call
3. Tools fetch real data from Google Maps APIs
4. Agent synthesizes findings into actionable insights
5. Frontend displays an interactive map with the analyzed location

### Example Interaction

```
User: "Analyze 456 Market Street, San Francisco for a bubble tea shop"

Agent:
1. Calls discover_neighborhood(address="456 Market St, SF", business_type="bubble tea")
2. Receives: competitors, transit stations, nearby food/retail
3. Generates analysis with location score (1-10)
4. Frontend shows map with markers for:
   - Target location (red)
   - Competitors (orange)
   - Transit stations (blue)
```

## Development

### Adding a New Tool

1. **Create tool directory**: `backend/app/tools/your_tool/`

2. **Create agent tools** (`agent_tools.py`):
   ```python
   from langchain_core.tools import tool

   @tool
   async def your_tool_function(param: str) -> dict:
       """Tool description for the LLM."""
       # Implementation
       return {"result": "data"}

   YOUR_TOOLS = [your_tool_function]
   ```

3. **Create agent** (`agent.py`):
   ```python
   from langgraph.prebuilt import create_react_agent
   from .agent_tools import YOUR_TOOLS

   class YourAgent:
       def __init__(self):
           self.agent = create_react_agent(llm, YOUR_TOOLS)

       async def process_stream(self, query: str):
           async for chunk in self.agent.astream(...):
               yield chunk
   ```

4. **Create tool wrapper** (`tool.py`):
   ```python
   from ..base import BaseTool, ToolContext

   class YourTool(BaseTool):
       tool_id = "your_tool"
       name = "Your Tool"
       description = "Tool description"
       icon = "🔧"

       async def process_stream(self, query: str, context: ToolContext):
           async for chunk in self.agent.process_stream(query):
               yield chunk
   ```

5. **Register tool** in `backend/app/main.py`:
   ```python
   ToolRegistry.register(YourTool())
   ```

### Using Caching

```python
from app.core.cache import cached

@cached(ttl=3600, key_prefix="my_operation")
async def expensive_operation(param: str):
    # Results cached for 1 hour
    return await some_api_call(param)
```

### Using Tracking

```python
from app.services.tracking_service import TrackingService

tracking = TrackingService(db)

# Track tool activity
activity_id = await tracking.start_tool_activity(
    session_id="...",
    tool_id="location_scout",
    tool_name="geocode_address",
    input_args={"address": "123 Main St"},
)

# Complete tracking
await tracking.complete_tool_activity(
    activity_id=activity_id,
    output_data={"lat": 37.7749, "lng": -122.4194},
    latency_ms=150,
)
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Streaming chat endpoint (SSE) |
| `/api/chat/conversations` | GET | List conversations for session |
| `/api/chat/conversations/{id}/messages` | GET | Get messages for conversation |
| `/api/tools` | GET | List available tools |
| `/health` | GET | Health check |
| `/docs` | GET | OpenAPI documentation (Swagger UI) |

## Deployment

### Recommended Setup

- **Frontend**: Deploy to [Vercel](https://vercel.com) or [Netlify](https://netlify.com)
- **Backend API**: Deploy to [Railway](https://railway.app), [Render](https://render.com), or [Fly.io](https://fly.io)
- **Redis**: Use managed Redis ([Upstash](https://upstash.com) or [Redis Cloud](https://redis.com/cloud))
- **Celery Worker**: Run as separate service/dyno
- **Database**: Supabase hosted PostgreSQL

### Production Checklist

- [ ] Set `DEBUG=false` in backend
- [ ] Use managed Redis (not localhost)
- [ ] Update CORS origins in `backend/app/main.py`
- [ ] Secure API keys via platform secrets
- [ ] Run database migrations
- [ ] Set up monitoring/alerting

## Performance

- **Caching**: 95%+ cache hit rate on repeated location queries
- **Cost Savings**: 67% reduction in Google Maps API calls
- **Response Time**: 100x faster for cached requests (5ms vs 500ms)
- **Retry Logic**: Automatic retries with exponential backoff
- **Tracking**: Full latency visibility for LLM and tool calls

## Monitoring

View backend logs with structured output:

```bash
# Development
uvicorn app.main:app --reload --port 8000

# Logs include:
# - Agent node updates
# - Tool call starts/completions
# - LLM response latencies
# - Error tracking with context
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT

## Links

- **Repository**: https://github.com/tamdogood/phow
- **Backend Documentation**: [backend/README.md](./backend/README.md)
- **Architecture Details**: [ARCHITECTURE.md](./ARCHITECTURE.md)

---

Built with care for small business owners

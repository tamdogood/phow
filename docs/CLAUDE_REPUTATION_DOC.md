# CLAUDE_REPUTATION_DOC — PHOW Reputation Hub Codebase Context

## Purpose

This document captures the full codebase exploration performed before implementing the Reputation Hub feature. It serves as the architectural reference for all sprint work.

---

## 1. Existing Architecture Summary

### Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15 App Router, TypeScript, Tailwind CSS, shadcn/ui |
| Backend | Python FastAPI, layered architecture (Repo → Service → Route) |
| Database | Supabase (PostgreSQL) |
| Cache | Redis (async, `@cached()` decorator) |
| Background | Celery + Redis broker |
| LLM | LangChain (OpenAI / Anthropic configurable) |
| Auth | Supabase Auth (optional), anonymous `session_id` via localStorage |

### Backend Directory Structure

```
backend/app/
├── main.py                         # FastAPI app, lifespan, CORS, router registration
├── api/
│   ├── deps.py                     # DI providers (get_supabase, get_chat_service, etc.)
│   └── routes/
│       ├── __init__.py             # Exports: chat_router, tools_router, business_profile_router, dashboard_router, community_router
│       ├── chat.py                 # SSE streaming chat
│       ├── tools.py                # Tool CRUD
│       ├── business_profile.py     # Business profile endpoints
│       ├── dashboard.py            # Dashboard aggregation
│       └── community.py            # Community posts
├── core/
│   ├── config.py                   # Pydantic Settings (env vars)
│   ├── cache.py                    # Redis CacheManager + @cached decorator
│   ├── llm.py                      # LangChain LLM factory
│   ├── logging.py                  # Structlog setup
│   └── tool_registry.py            # Tool registration
├── models/
│   └── chat.py                     # ChatRequest, Message, Conversation, ChatResponse
├── repositories/
│   ├── base.py                     # BaseRepository(ABC) — holds self.db (Supabase Client)
│   ├── conversation_repository.py
│   ├── message_repository.py
│   ├── business_profile_repository.py
│   ├── llm_response_repository.py
│   ├── tool_activity_repository.py
│   ├── community_repository.py
│   └── location_intelligence_repository.py
├── services/
│   ├── __init__.py                 # Exports: ChatService, TrackingService, CommunityService
│   ├── chat_service.py
│   ├── tracking_service.py
│   ├── community_service.py
│   └── business_profile_service.py
├── tools/                          # BaseTool → process(), process_stream(), get_system_prompt()
├── clients/                        # External API clients
└── workers/
    ├── celery_app.py
    └── tasks.py
```

### Frontend Directory Structure

```
frontend/src/
├── app/
│   ├── layout.tsx                  # Root layout (Inter + JetBrains Mono, Providers wrapper)
│   ├── page.tsx                    # Home/landing
│   ├── globals.css                 # All custom CSS classes
│   ├── app/page.tsx                # Chat interface
│   ├── dashboard/page.tsx          # Dashboard with ScoreCard, CompetitorCard, etc.
│   ├── business-setup/page.tsx     # Business profile setup
│   └── community/                  # Community pages
├── components/
│   ├── chat/                       # Chat.tsx, ChatInput.tsx, ChatMessage.tsx, ToolSelector.tsx
│   ├── tools/                      # CompetitorWidget, MarketValidatorWidget
│   ├── dashboard/                  # CommunityWidget, AddCompetitorModal
│   ├── landing/                    # Landing page components
│   ├── widgets/                    # Reusable widget components
│   └── ui/                         # shadcn/ui primitives (button, card, input)
├── contexts/
│   └── AuthContext.tsx             # Supabase auth provider (user, session, signIn, signOut)
├── lib/
│   ├── api.ts                      # All backend API functions (fetch + SSE)
│   ├── session.ts                  # Anonymous session via localStorage UUID
│   └── supabase.ts                 # Supabase client init
└── types/
    └── index.ts                    # All TypeScript interfaces
```

---

## 2. Key Patterns to Follow

### Repository Pattern

```python
# All repos extend BaseRepository which holds self.db (Supabase Client)
class SomeRepository(BaseRepository):
    async def create(self, **kwargs) -> dict[str, Any]:
        result = self.db.table("table_name").insert(kwargs).execute()
        return result.data[0] if result.data else {}

    async def get_by_id(self, id: str) -> dict[str, Any] | None:
        result = self.db.table("table_name").select("*").eq("id", id).execute()
        return result.data[0] if result.data else None
```

### Service Pattern

```python
class SomeService:
    def __init__(self, db: Client):
        self.repo = SomeRepository(db)

    async def do_work(self, param: str):
        return await self.repo.create(param=param)
```

### Dependency Injection (deps.py)

```python
def get_some_service(db: Client = Depends(get_supabase)) -> SomeService:
    return SomeService(db)
```

### Route Registration (main.py)

```python
from .api.routes import some_router
app.include_router(some_router, prefix="/api")
```

### Frontend API Pattern (api.ts)

```typescript
export async function fetchSomething(params: Params): Promise<Result> {
  const response = await fetch(`${API_URL}/api/endpoint?${new URLSearchParams(params)}`);
  if (!response.ok) throw new Error("Failed");
  const data = await response.json();
  return data.result;
}
```

### Frontend Component Pattern

```typescript
"use client";
import { useState, useEffect } from "react";

export function SomeComponent({ prop }: { prop: string }) {
  const [state, setState] = useState<Type>(initial);
  // ...
  return <div className="dark-card p-6">...</div>;
}
```

---

## 3. CSS Classes Available (globals.css)

| Class | Purpose |
|---|---|
| `.dark-card` | `bg-[#111111]`, 1px `rgba(255,255,255,0.05)` border, `border-radius: 1rem` |
| `.dark-header` | `rgba(10,10,10,0.8)` bg, `backdrop-filter: blur(12px)`, bottom border |
| `.hover-lift` | `translateY(-4px)` + shadow on hover |
| `.grid-pattern` | Subtle dashed grid overlay |
| `.animate-fade-in-up` | Fade + slide up, 0.8s |
| `.animate-shimmer` | Loading skeleton shimmer |
| `.ai-insight-pill` | Purple gradient with glow |
| `.progress-bar-gradient-{green,blue,yellow,red}` | Colored progress bars |
| `.text-accent-blue` | `#3B82F6` |

---

## 4. Database Schema (Existing Tables)

### Migrations: `supabase/migrations/001–005`

- **conversations** — `id`, `session_id`, `user_id`, `tool_id`, `title`, timestamps
- **messages** — `id`, `conversation_id` (FK), `role`, `content`, `metadata` (JSONB)
- **business_profiles** — `id`, `session_id`, `user_id`, business fields, `location_lat/lng/place_id`
- **tracked_competitors** — `id`, `business_profile_id` (FK), `place_id`, `name`, `address`, `rating`, `review_count`, `price_level`, `strengths[]`, `weaknesses[]`, UNIQUE on `(business_profile_id, place_id)`
- **market_analyses** — `id`, `business_profile_id`, `viability_score`, JSONB fields for demographics/demand/competition
- **competitor_analyses** — `id`, `business_profile_id`, `overall_competition_level`, JSONB fields
- **llm_responses** — tracking LLM calls
- **tool_activities** — tracking tool invocations
- **community_posts** / **post_comments** — community forum

---

## 5. Key Files to Modify (Exact Paths)

| File | What Changes |
|---|---|
| `backend/app/core/config.py` | Add `review_token_encryption_key`, `google_oauth_client_id`, `google_oauth_client_secret`, `facebook_app_id`, `facebook_app_secret` |
| `backend/app/main.py` | Import + register `reviews_router` |
| `backend/app/api/deps.py` | Add `get_review_service()`, `get_connection_service()`, `get_analytics_service()` |
| `backend/app/api/routes/__init__.py` | Export `reviews_router` |
| `backend/app/repositories/__init__.py` | Export new review repositories |
| `backend/app/services/__init__.py` | Export new review services |
| `frontend/src/types/index.ts` | Add `ReviewSource`, `Review`, `ReviewResponse`, `ReviewNotification`, `AlertSettings` interfaces |
| `frontend/src/lib/api.ts` | Add all `/api/reviews/*` functions |
| `frontend/src/app/dashboard/page.tsx` | Add "Reputation" nav link in header |

---

## 6. Dashboard Navigation Pattern (Reference)

From `dashboard/page.tsx` header (lines 298–328):

```tsx
<header className="dark-header fixed top-0 left-0 right-0 z-50 px-6 py-4">
  <div className="mx-auto max-w-6xl flex items-center justify-between">
    <div className="flex items-center gap-3">
      <Link href="/" className="text-xl font-bold text-white">PHOW</Link>
      <span className="hidden sm:inline-flex ... text-[10px] ...">Dashboard</span>
    </div>
    <div className="flex items-center gap-3">
      <Link href="/community" className="px-4 py-2 text-white/70 ...">Community</Link>
      <Link href="/business-setup" className="px-4 py-2 text-white/70 ...">My Business</Link>
      <Link href="/app" className="... bg-white text-black ...">New Analysis</Link>
    </div>
  </div>
</header>
```

The "Reputation" link will be inserted between "Community" and "My Business".

---

## 7. Feature Spec Reference

Full feature specification: See plan at `.claude/plans/jolly-dreaming-dragon.md`
Existing requirement docs:
- `docs/PHOW_REPUTATION_HUB_REQUIREMENTS.md`
- `docs/COMBINED_PHOW_REVIEW_MANAGEMENT_SPEC.md`

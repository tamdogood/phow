# Frontend CLAUDE.md

This file provides detailed guidance for working with the PHOW frontend codebase. See the root `CLAUDE.md` for project-wide principles and architecture overview.

## Frontend Architecture

### Stack & Dependencies
- **Framework**: Next.js 16.1+ with App Router
- **Language**: TypeScript 5+
- **Styling**: Tailwind CSS 4+ with PostCSS
- **UI Components**: shadcn/ui (Radix UI primitives)
- **Icons**: Lucide React
- **Maps**: `@react-google-maps/api` for Google Maps integration
- **Markdown**: `react-markdown` for rendering LLM responses
- **State Management**: React hooks (useState, useEffect)
- **HTTP Client**: Native Fetch API with SSE support
- **Code Quality**: ESLint with Next.js config

### Directory Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── layout.tsx          # Root layout
│   │   ├── page.tsx            # Home page (tool selector + chat)
│   │   └── globals.css         # Global styles
│   ├── components/
│   │   ├── chat/               # Chat UI components
│   │   │   ├── Chat.tsx        # Main chat container
│   │   │   ├── ChatInput.tsx   # Message input
│   │   │   ├── ChatMessage.tsx # Message display
│   │   │   ├── QuickHints.tsx  # Example query suggestions
│   │   │   ├── ToolBar.tsx     # Tool switching
│   │   │   ├── ToolSelector.tsx # Initial tool selection
│   │   │   ├── MapWidget.tsx   # Google Maps widget
│   │   │   └── index.ts        # Exports
│   │   ├── tools/              # Tool-specific widgets
│   │   │   ├── CompetitorWidget.tsx
│   │   │   └── MarketValidatorWidget.tsx
│   │   └── ui/                 # shadcn/ui components
│   │       ├── button.tsx
│   │       ├── card.tsx
│   │       └── input.tsx
│   ├── lib/                    # Utilities
│   │   ├── api.ts              # Backend API client (SSE support)
│   │   └── session.ts          # Anonymous session management
│   └── types/                  # TypeScript types
│       └── index.ts            # Shared type definitions
├── public/                     # Static assets
├── components.json             # shadcn/ui config
├── next.config.ts              # Next.js configuration
├── tailwind.config.ts          # Tailwind configuration
├── tsconfig.json               # TypeScript configuration
└── package.json                # Dependencies
```

## Core Patterns

### 1. Component Structure
All components are client components (use `"use client"` directive):
```typescript
"use client";

import { useState } from "react";

export function YourComponent({ prop }: { prop: string }) {
  const [state, setState] = useState<string>("");
  
  return <div>{/* JSX */}</div>;
}
```

### 2. API Client Pattern
All backend communication via `src/lib/api.ts`:
```typescript
import { sendChatMessage } from "@/lib/api";

await sendChatMessage(sessionId, toolId, message, conversationId, {
  onChunk: (content) => { /* handle chunk */ },
  onDone: (conversationId) => { /* handle completion */ },
  onError: (error) => { /* handle error */ },
});
```

**API Functions:**
- `fetchTools()`: Get available tools
- `fetchConversations(sessionId)`: Get user conversations
- `fetchMessages(conversationId)`: Get conversation messages
- `sendChatMessage(...)`: Send message with SSE streaming

### 3. Session Management
Anonymous sessions via `src/lib/session.ts`:
```typescript
import { getSessionId } from "@/lib/session";

const sessionId = getSessionId(); // Gets or creates UUID, stored in localStorage
```

Session ID is stored in `localStorage` under key `"phow_session_id"`.

### 4. Type Definitions
All types in `src/types/index.ts`:
```typescript
export interface Tool {
  id: string;
  name: string;
  description: string;
  icon: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  metadata?: Record<string, unknown>;
  created_at: string;
}

export interface Conversation {
  id: string;
  session_id: string;
  tool_id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}
```

### 5. SSE Streaming Pattern
Chat uses Server-Sent Events for streaming responses:
```typescript
const response = await fetch(`${API_URL}/api/chat`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ session_id, tool_id, message, conversation_id }),
});

const reader = response.body?.getReader();
const decoder = new TextDecoder();
let buffer = "";

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  buffer += decoder.decode(value, { stream: true });
  const lines = buffer.split("\n");
  buffer = lines.pop() || "";
  
  for (const line of lines) {
    if (line.startsWith("data:")) {
      const data = JSON.parse(line.slice(5).trim());
      if (data.content) callbacks.onChunk(data.content);
      if (data.conversation_id) callbacks.onDone(data.conversation_id);
      if (data.error) callbacks.onError(data.error);
    }
  }
}
```

### 6. Dynamic Imports
Heavy components use dynamic imports for code splitting:
```typescript
import dynamic from "next/dynamic";

const Chat = dynamic(() => import("@/components/chat").then((mod) => ({ default: mod.Chat })), {
  ssr: false,
});
```

## Component Details

### Chat Component (`Chat.tsx`)
Main chat interface:
- Manages message state and streaming
- Handles tool switching
- Displays welcome message with tool capabilities
- Shows quick hints for example queries
- Auto-scrolls to bottom on new messages

**Props:**
- `toolId`: Current tool identifier
- `toolName`: Display name
- `toolDescription`: Tool description
- `toolIcon`: Emoji icon
- `onSwitchTool?`: Callback for tool switching

**State:**
- `messages`: Array of `LocalMessage` objects
- `isLoading`: Loading state
- `conversationId`: Current conversation ID
- `streamingContent`: Current streaming text
- `inputValue`: Input field value

### ChatInput Component (`ChatInput.tsx`)
Message input field with send button:
- Disabled during loading
- Handles Enter key submission
- Customizable placeholder

### ChatMessage Component (`ChatMessage.tsx`)
Renders individual messages:
- User messages: Right-aligned, blue background
- Assistant messages: Left-aligned, white background
- Streaming indicator for in-progress messages
- Markdown rendering for assistant messages

### QuickHints Component (`QuickHints.tsx`)
Displays example queries:
- Fetches hints from tool metadata
- Clickable buttons that populate input
- Hidden during loading

### ToolSelector Component (`ToolSelector.tsx`)
Initial tool selection screen:
- Grid of available tools
- Fetches tools from `/api/tools` endpoint
- Displays tool name, description, and icon

### ToolBar Component (`ToolBar.tsx`)
Tool switching dropdown:
- Shows current tool
- Dropdown to switch to other tools
- Used in chat header

## Styling

### Tailwind CSS
- Utility-first approach
- Custom colors defined in `globals.css`
- Responsive design with mobile-first breakpoints
- Dark mode support (if needed)

### Component Styling
- Use Tailwind classes directly in JSX
- Extract repeated patterns to constants if needed
- Follow existing color scheme:
  - Primary: Blue/Indigo gradient
  - Background: White/Gray-50
  - Text: Gray-900/Gray-600
  - Borders: Gray-200

## State Management

### Local State
Use React hooks for component state:
```typescript
const [state, setState] = useState<Type>(initialValue);
```

### Global State
No global state management library. Use:
- Props drilling for parent-child communication
- URL params for shareable state (if needed)
- localStorage for persistence (session ID)

## Environment Variables

### Next.js Environment Variables
- `NEXT_PUBLIC_API_URL`: Backend API URL (default: "http://localhost:8000")

Access via: `process.env.NEXT_PUBLIC_API_URL`

## API Integration

### Base URL
Defined in `src/lib/api.ts`:
```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
```

### Endpoints
- `GET /api/tools`: List available tools
- `POST /api/chat`: Send message (SSE stream)
- `GET /api/chat/conversations?session_id=...`: List conversations
- `GET /api/chat/conversations/{id}/messages`: Get messages

### Error Handling
- Network errors: Display user-friendly error message
- API errors: Show error in chat as assistant message
- SSE errors: Trigger `onError` callback

## Google Maps Integration

### MapWidget Component
Uses `@react-google-maps/api`:
```typescript
import { GoogleMap, LoadScript, Marker } from "@react-google-maps/api";

<LoadScript googleMapsApiKey={process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || ""}>
  <GoogleMap>
    <Marker position={location} />
  </GoogleMap>
</LoadScript>
```

**Note**: Requires `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` environment variable.

## Code Style

### TypeScript
- Use type annotations for all props
- Prefer interfaces over types for object shapes
- Use `|` for union types
- Use `?` for optional properties
- Export types from `src/types/index.ts`

### React
- Use functional components only
- Use hooks for state and effects
- Extract reusable logic to custom hooks if needed
- Keep components focused and small

### Naming
- Components: PascalCase (`ChatMessage.tsx`)
- Functions: camelCase (`handleSend`)
- Constants: UPPER_SNAKE_CASE (`API_URL`)
- Files: Match component name

### Imports
- Use absolute imports with `@/` alias
- Group imports: React, Next.js, third-party, local
- Use named exports for components

## Common Tasks

### Adding a New Component
1. Create file in appropriate directory (`components/chat/`, `components/tools/`, etc.)
2. Export component: `export function YourComponent() { ... }`
3. Add to `index.ts` if in a directory with exports
4. Import where needed: `import { YourComponent } from "@/components/...";`

### Adding a New Tool Widget
1. Create `components/tools/YourToolWidget.tsx`
2. Accept relevant props (data, onAction, etc.)
3. Style with Tailwind classes
4. Import in tool-specific components as needed

### Modifying Chat Flow
1. Update `Chat.tsx` for main flow changes
2. Update `ChatInput.tsx` for input changes
3. Update `ChatMessage.tsx` for message display changes
4. Update `api.ts` if API contract changes

### Adding a New API Endpoint
1. Add function to `src/lib/api.ts`
2. Use TypeScript types for request/response
3. Handle errors appropriately
4. Export from `api.ts`

### Styling Changes
1. Use Tailwind utility classes
2. Add custom styles to `globals.css` if needed
3. Update component styles directly
4. Maintain consistent color scheme

## Development Commands

```bash
# Install dependencies
npm install

# Run dev server (port 3000)
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run linter
npm run lint
```

## Key Files Reference

- **Entry Point**: `src/app/page.tsx` - Home page with tool selector and chat
- **Chat Component**: `src/components/chat/Chat.tsx` - Main chat interface
- **API Client**: `src/lib/api.ts` - Backend communication
- **Session**: `src/lib/session.ts` - Session management
- **Types**: `src/types/index.ts` - TypeScript definitions
- **Layout**: `src/app/layout.tsx` - Root layout
- **Styles**: `src/app/globals.css` - Global CSS

## Important Notes

- **All components are client components** - Use `"use client"` directive
- **Use TypeScript types** - Define types in `src/types/index.ts`
- **Handle loading states** - Show loading indicators during API calls
- **Handle errors gracefully** - Display user-friendly error messages
- **Stream responses** - Use SSE for real-time streaming
- **Mobile responsive** - Ensure components work on mobile devices
- **Accessibility** - Use semantic HTML and ARIA attributes
- **Performance** - Use dynamic imports for heavy components
- **Follow existing patterns** - Match code style and structure of similar components

## Tool-Specific Features

### Location Scout
- Map widget for location visualization
- Competition density display
- Transit accessibility indicators

### Market Validator
- Demographics charts/widgets
- Market size visualization
- Competition saturation score

### Competitor Analyzer
- Competitor list display
- Review sentiment visualization
- Price vs quality positioning

Each tool may have custom widgets in `components/tools/` directory.

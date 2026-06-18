# PHOW Design System (dark theme + shadcn/ui)

**Updated:** June 2026 · Source of truth: `frontend/src/app/globals.css`

PHOW ships a single, cohesive **dark** theme built on shadcn/ui tokens. The whole app is themed from one file (`globals.css`) + a small set of shared surface classes, so visual changes propagate everywhere. `html` is permanently `class="dark"`.

## Palette & tokens (the `.dark` block in `globals.css`)
Layered near-black elevation + one confident accent:

| Token | Value | Use |
|---|---|---|
| `--background` | `#0a0a0b` | App background (matches legacy `bg-[#0a0a0a]`) |
| `--card` / `--phow-surface` | `#151518` / `#131316` | Cards / panels |
| `--phow-surface-2` | `#18181c` | Slightly elevated widgets |
| `--popover` | `#161619` | Menus, dialogs |
| `--primary` | `#3b82f6` (azure) | Accent, primary buttons, focus |
| `--foreground` | `#ededf0` | Primary text (soft white) |
| `--muted-foreground` | `#9a9aa4` | Secondary text |
| `--border` / `--phow-border` | `white / 8%` | Hairline borders |
| `--phow-border-strong` | `white / 14%` | Hover borders |
| `--ring` | `azure / 60%` | Focus ring |
| `--radius` | `0.75rem` | Base radius (shadcn scales off this) |

`--chart-1..5` = blue / emerald / amber / violet / rose (consistent data-viz palette).
`--phow-accent` is an RGB triplet (`59,130,246`) for `rgba(var(--phow-accent), …)` usage.

## Elevation / surface classes
Use these everywhere instead of ad-hoc hex backgrounds — they're the unified, premium surface system:
- **`.dark-card`** — standard panel (gradient sheen + hairline border + soft shadow, brighter border on hover). Default building block.
- **`.widget-card`** — a touch more elevated, for data widgets.
- **`.glass` / `.glass-card` / `.glass-input` / `.glass-header`** — translucent blur surfaces (landing, overlays).
- **`.dark-header`** — sticky blurred app header (used by `AppHeader`).
- **`.hover-lift`** — subtle lift + shadow on hover for interactive cards.

## Base-layer polish (automatic, app-wide)
Defined in `globals.css`: antialiased fonts + Inter (`--font-geist-sans`), tightened heading tracking, app-wide thin scrollbars, azure `::selection`, accent `:focus-visible` rings for links/buttons, and a faint fixed radial glow on `body` for depth. Print styles (`@media print`) flatten the theme to white for the feasibility PDF.

## shadcn/ui
- Config: `components.json` (new-york, neutral, CSS variables). `cn()` in `lib/utils.ts`.
- Primitives in `components/ui/`: `button`, `card`, `input` (pre-existing) + `badge`, `tabs`, `skeleton`, `dialog` (added). `sonner` toaster mounted in `app/layout.tsx`.
- All primitives read the tokens above, so they're automatically on-theme. **Build new UI with these primitives + the surface classes** — don't hand-roll buttons/badges/modals.
- Deps for the added primitives: `@radix-ui/react-dialog`, `@radix-ui/react-tabs`, `sonner` (in `package.json` — run `npm install`).

## Conventions
- **Accent sparingly** — one azure accent for primary actions/active states; everything else is grayscale + hairline borders.
- Severity colors: urgent = red, watch = amber, info/positive = blue/emerald (see `lib/radar-api.ts::severityStyle`).
- Reference surfaces built to this standard: `AppHeader`, `app/radar/page.tsx`, `components/dashboard/RadarWidget.tsx`, `components/report/ReportView.tsx`.

## Extending
Add a shadcn primitive: `npx shadcn@latest add <name>` (it picks up `components.json` + tokens), then `npm install` any new Radix dep. Prefer adjusting **tokens** over hardcoded colors so the change is global. Keep `dark-card`/`widget-card` for domain widgets; migrate ad-hoc `bg-[#…]`/`bg-slate-*` panels to these classes over time.

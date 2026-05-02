# Technical Context: Hybrid Web + AI Agent Platform

## Technology Stack

| Technology       | Version   | Purpose                                 |
|------------------|-----------|-----------------------------------------|
| Next.js          | 16.x      | React framework with App Router         |
| React            | 19.x      | UI library                              |
| TypeScript       | 5.9.x     | Type-safe JavaScript                    |
| Tailwind CSS     | 4.x       | Utility-first CSS                       |
| Bun              | Latest    | Package manager & runtime (frontend)    |
| **Python**       | 3.11+     | Bridge agent runtime                    |
| aiohttp          | latest    | Async HTTP client (LM Studio, Obsidian) |
| aiosqlite        | latest    | Async SQLite driver                     |
| python-telegram-bot | 20.x  | Telegram bot framework                  |

## Development Environment

### Frontend Prerequisites

- Bun installed (`curl -fsSL https://bun.sh/install | bash`)
- Node.js 20+ (for compatibility)

### Backend Prerequisites (Bridge Agent)

- Python 3.11+ and venv
- LM Studio running locally (`http://localhost:1234`)
- Obsidian vault (optional REST plugin for live refresh)

### Commands

#### Frontend (Next.js)

```bash
bun install        # Install dependencies
bun dev            # Start dev server (http://localhost:3000)
bun build          # Production build
bun start          # Start production server
bun lint           # Run ESLint
bun typecheck      # Run TypeScript type checking
```

#### Backend (Bridge)

```bash
cd bridge
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# Create .env from example
cp .env.example .env
# Edit .env with your TELEGRAM_BOT_TOKEN and paths

python main.py
```

## Project Configuration

### Next.js Config (`next.config.ts`)

- App Router enabled
- Default settings for flexibility

### TypeScript Config (`tsconfig.json`)

- Strict mode enabled
- Path alias: `@/*` → `src/*`
- Target: ESNext

### Tailwind CSS 4 (`postcss.config.mjs`)

- Uses `@tailwindcss/postcss` plugin
- CSS-first configuration (v4 style)

### ESLint (`eslint.config.mjs`)

- Uses `eslint-config-next`
- Flat config format

### Bridge Agent (`bridge/config.py`)

All configuration via environment variables:
- `TELEGRAM_BOT_TOKEN` (required)
- `ALLOWED_USERS` (comma-separated Telegram user IDs)
- `LM_STUDIO_BASE_URL` (default `http://localhost:1234/v1`)
- `LM_STUDIO_MODEL`
- `OBSIDIAN_VAULT_PATH` (required)
- `OBSIDIAN_REST_URL` (optional)
- `AGENT_NAME`, `AGENT_VIBE`, `AGENT_EMOJI`, `AGENT_SOUL`
- `HEARTBEAT_INTERVAL`, `SYNC_INTERVAL`, `TYPING_INDICATOR_INTERVAL`

## Key Dependencies

### Frontend Production

```json
{
  "next": "^16.1.3",
  "react": "^19.2.3",
  "react-dom": "^19.2.3"
}
```

### Frontend Dev

```json
{
  "typescript": "^5.9.3",
  "@types/node": "^24.10.2",
  "@types/react": "^19.2.7",
  "@types/react-dom": "^19.2.3",
  "@tailwindcss/postcss": "^4.1.17",
  "tailwindcss": "^4.1.17",
  "eslint": "^9.39.1",
  "eslint-config-next": "^16.0.0"
}
```

### Backend (Bridge Agent)

```
python-telegram-bot==20.7
aiohttp==3.9.3
aiosqlite==0.19.0
python-dotenv==1.0.1
```

## File Structure

```
/
├── .gitignore              # Git ignore rules
├── package.json            # Frontend deps & scripts
├── bun.lock                # Bun lockfile
├── next.config.ts          # Next.js configuration
├── tsconfig.json           # TypeScript configuration
├── postcss.config.mjs      # PostCSS (Tailwind) config
├── eslint.config.mjs       # ESLint configuration
├── .kilocode/              # AI memory bank & recipes
├── public/                 # Static assets
│   └── .gitkeep
├── src/                    # Frontend source code
│   └── app/
│       ├── layout.tsx
│       ├── page.tsx
│       ├── globals.css
│       └── favicon.ico
├── bridge/                 # Python bridge agent (backend)
│   ├── main.py
│   ├── config.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── llm/client.py
│   ├── memory/
│   ├── obsidian/
│   ├── agent/
│   └── bot/
└── BrainVault/             # Obsidian vault (generated at runtime)
    ├── Daily Note/
    ├── Memory/
    ├── People/
    ├── Agent/
    └── Knowledge/
```

## Technical Constraints

### Frontend Starting Point

- Minimal structure - expand as needed
- No database by default (use recipe to add)
- No authentication by default (add when needed)

### Bridge Agent

- Single-user design (extendable only with schema changes)
- SQLite as per‑user hot cache (WAL mode)
- Obsidian as human‑readable cold store (markdown)
- LM Studio as LLM provider (OpenAI‑compatible API)
- Telegram as sole UI interface

### Browser Support

- Modern browsers (ES2020+)
- No IE11 support

## Performance Considerations

### Frontend

- Image Optimization via Next.js `Image`
- Server Components reduce client JavaScript
- Streaming and Suspense for better UX

### Bridge Agent

- Async I/O throughout (aiohttp/aiosqlite)
- Typing indicator loop every ~4s (configurable)
- Non-blocking vault sync (queue-based)
- SQLite WAL for concurrent read/write

## Deployment

### Frontend Build Output

- Server‑rendered pages by default
- Can be configured for static export

### Bridge Agent

- Long‑running process (systemd/docker recommended)
- Requires persistent storage for SQLite & vault
- Env vars via `.env` or system environment

### Environment Variables

- Frontend: None required for base template
- Bridge: See `bridge/config.py` for full list


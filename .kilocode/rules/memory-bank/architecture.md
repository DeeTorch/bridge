# System Patterns: Hybrid Web + AI Agent Platform

## Architecture Overview

This repository contains two integrated subsystems:

### 1. Next.js Frontend (src/)

```
src/
├── app/                    # Next.js App Router
│   ├── layout.tsx          # Root layout + metadata
│   ├── page.tsx            # Home page
│   ├── globals.css         # Tailwind imports + global styles
│   └── favicon.ico         # Site icon
└── (expand as needed)
    ├── components/         # React components (add when needed)
    ├── lib/                # Utilities and helpers (add when needed)
    └── db/                 # Database files (add via recipe)
```

Frontend is a standard Next.js 16 starter. It can serve as a dashboard to visualize the Obsidian vault or manage the agent if extended.

### 2. Bridge Telegram Agent (bridge/)

```
bridge/
├── main.py                        # Entry point
├── config.py                      # Env validation & constants
├── requirements.txt
├── .env.example
│
├── llm/
│   └── client.py                  # LM Studio client, typing indicator loop, retry
│
├── memory/
│   ├── database.py                # SQLite: messages, summaries, knowledge, profile, sync queue
│   └── summarizer.py              # Rolling compression + long-term knowledge extraction
│
├── obsidian/
│   ├── vault.py                   # Filesystem R/W — primary interface
│   ├── rest.py                    # REST API client — live refresh fallback
│   ├── formatter.py               # Obsidian markdown: frontmatter, wikilinks, tags
│   └── sync.py                    # Async orchestrator: SQLite → Obsidian
│
├── agent/
│   ├── identity.py                # Agent IDENTITY.md & SOUL.md maintenance
│   ├── profile.py                 # User profile auto‑updates
│   ├── knowledge.py               # Topic/fact extraction → Knowledge/ notes
│   └── heartbeat.py               # Scheduler: daily note rollover, periodic jobs
│
└── bot/
    └── handlers.py                # Telegram command + message handlers (thin)
```

### Two‑Layer Memory Model

```
Telegram ──► Agent Runtime ──► SQLite (hot cache, fast R/W)
                                    │
                                    ▼ async sync
                              Obsidian Vault (cold store, human‑readable)
```

- **SQLite**: real‑time operations; no user waits on file I/O.
- **Obsidian**: async sync after each interaction; REST plugin ping for live refresh if available.
- Filesystem first: Works even if Obsidian is closed; zero plugin dependency.

## Key Design Patterns

### Bridge Agent Patterns

#### 1. Two‑Layer Memory
- Hot: SQLite WAL mode for concurrent reads/writes.
- Cold: Markdown files in Obsidian vault with frontmatter and wikilinks.

#### 2. Async Sync Queue
- DB `sync_queue` table decouples message processing from vault writes.
- Background task drains queue every few seconds; failures retry.

#### 3. Knowledge Extraction
- After each exchange, LLM identifies atomic facts → stored as `Knowledge/<slug>.md`.
- Enables true graph brain: daily notes link to knowledge notes, people, memory.

#### 4. Typing Indicator Loop
- Background asyncio task sends `typing` action every ~4s until LLM responds.

#### 5. Agent as Bot
- Bot handlers are thin; agent logic lives in `agent/` modules.
- Identity, profile, knowledge, heartbeat each have single responsibility.

### Next.js Patterns (unchanged from template)

*(The existing Next.js patterns remain — see below.)*


# Product Context: Hybrid Web + AI Agent Platform

## Why This Project Exists

Starting a new Next.js project involves boilerplate setup, configuration decisions, and establishing patterns. This template provides a clean, opinionated starting point that eliminates setup friction and establishes best practices from the start. It's optimized for AI-assisted development, where an AI can quickly extend the template based on user requirements.

Additionally, this project includes a **Bridge Telegram Agent** — a personal AI assistant that runs as a separate Python service, connecting Telegram to a local Obsidian vault. This dual approach gives you both a modern web front-end and a conversational AI back-end that persists knowledge in a human‑readable, linked graph.

## Problems It Solves

1. **Setup Time**: Eliminates boilerplate configuration (TypeScript, Tailwind, ESLint) for web front‑end.
2. **Decision Fatigue**: Pre-made choices for tooling and patterns.
3. **AI Context**: Memory bank provides persistent context for AI assistants.
4. **Extensibility**: Recipe system for adding common features.
5. **Consistency**: Standardized project structure and conventions.
6. **Conversational AI**: Bridge agent gives you a ChatGPT‑like assistant that automatically writes to your Obsidian vault, creating a second brain without manual logging.

## How It Should Work (User Flow)

### Option A: Web Front‑end
1. User starts with this template
2. User describes what they want to build to AI assistant
3. AI adds pages, components, and features as needed
4. AI uses recipes for common additions (database, auth)
5. User previews changes via hot reload
6. Iterate until satisfied
7. Deploy

### Option B: Telegram Agent (Bridge)
1. User sets up LM Studio + Obsidian vault
2. User runs `python bridge/main.py`
3. User chats with the agent on Telegram
4. Agent instantly saves conversations to Obsidian (Daily Notes)
5. Agent extracts knowledge nuggets into `Knowledge/` and updates user profile in `People/USER.md`
6. Over time, a rich, linked personal knowledge base grows automatically

## Key User Experience Goals

- **Zero to Feature Fast**: Get building immediately, no setup required
- **AI‑Friendly**: Memory bank and recipes make AI assistance effective
- **Flexible Foundation**: Can become any type of application (web or agent)
- **Best Practices Built‑In**: TypeScript strict mode, ESLint, clean structure
- **Persistent Conversational Memory**: Talk naturally; your words are automatically organized

## What This Project Provides

1. **Frontend**: Clean Next.js app structure ready for expansion
2. **Backend Agent**: Fully‑featured Telegram bridge with SQLite/Obsidian sync
3. **Type Safety**: Full TypeScript setup with strict mode
4. **Modern Styling**: Tailwind CSS 4 ready to use
5. **Code Quality**: ESLint configured
6. **Extensibility**: Recipe system for common features

## Integration Points

- **Database**: Use add-database recipe for Drizzle + SQLite (frontend)
- **Agent ↔ Vault**: Direct filesystem writes + optional REST plugin
- **Frontend ↔ Agent**: Both can read from the same SQLite DB and vault if needed (future)
- **Styling**: Tailwind CSS pre-configured
- **AI Assistance**: Memory bank for context persistence


# Project Brief: Hybrid Web + AI Agent Platform

## Purpose

This repository provides two complementary toolkits:

1. **Next.js Starter Template** — A modern front‑end foundation with TypeScript and Tailwind CSS 4, optimized for AI‑assisted development.
2. **Bridge Telegram Agent** — A Python service that runs a personal AI assistant accessible via Telegram, with automatic two‑layer memory (SQLite hot cache + Obsidian vault cold store).

Together they form a full‑stack platform for building web UIs while maintaining a conversational AI that builds a second brain in your Obsidian vault.

## Target Users

- Developers wanting a clean Next.js starting point
- Users building applications through AI‑assisted coding
- Teams needing a standardized, modern Next.js setup
- Individuals who want a personal AI assistant that writes to their notes

## Core Use Cases

### Frontend
Users describe what they want to build to an AI assistant, which expands the Next.js template by adding pages, components, dependencies, and features using recipes.

### Backend (Bridge)
Users chat with the AI on Telegram; every exchange is:
- Saved to SQLite for immediate context
- Appended to a daily note in Obsidian
- Analyzed for knowledge nuggets (stored as linked markdown notes)
- Used to update a long‑term user profile and rolling summary

## Key Requirements

### Must Have

- Modern Next.js 16 setup with App Router
- TypeScript for type safety
- Tailwind CSS 4 for styling
- ESLint for code quality
- Clean, minimal starting structure
- Bun as package manager
- Python Bridge Agent (Telegram integration)
- SQLite for realtime persistence
- Obsidian vault for human‑readable storage
- LM Studio compatibility (local LLM)

### Nice to Have

- Recipe system for common additions (database, auth)
- Memory bank for AI context persistence
- Obsidian REST plugin integration for live vault refresh
- Proactive heartbeat (daily note creation, periodic summarization)

## Success Metrics

- Clean, zero‑error TypeScript setup
- Passing lint and type checks
- Bridge agent starts reliably, connects to Telegram, responds
- All messages saved to both SQLite and Obsidian within seconds
- Knowledge graph grows with wikilinks and frontmatter

## Constraints

- Minimal dependencies by default (frontend)
- Framework: Next.js 16 + React 19 + Tailwind CSS 4
- Package manager: Bun (frontend), pip (backend)
- Python 3.11+ required for bridge


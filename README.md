# Hybrid Web + AI Agent Platform

A full-stack platform combining a Next.js frontend with a Python-based Telegram bridge agent that maintains conversation history and knowledge extraction capabilities.

## Features

- ⚡️ [Next.js 16](https://nextjs.org) frontend with App Router, TypeScript & Tailwind CSS 4
- 🤖 Python Telegram bridge agent with two-layer memory system (SQLite + Obsidian vault)
- 🧠 Automatic knowledge extraction and user profile updates from conversations
- 🔄 Async synchronization between hot cache (SQLite) and cold store (Obsidian)
- 💬 Rich Telegram bot interface with commands: /start, /clear, /status, /who, /remember, /open, /sync
- ❤️ Proactive heartbeat with daily note rollover and periodic summarization
- 📊 Observable vault structure with Daily Notes, Memory, People, Agent, Knowledge categories

## System Architecture

The platform consists of two main components:

1. **Frontend (Next.js)**: Clean Next.js 16 + TypeScript + Tailwind CSS 4 starter ready for UI development
2. **Backend Agent (Bridge)**: Fully implemented Telegram bot with two-layer memory (SQLite + Obsidian vault)

## Getting Started

### Frontend Development

First, install the dependencies:

```bash
bun install
```

Then, run the development server:

```bash
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

### Backend Agent (Bridge)

The bridge agent requires Python dependencies:

```bash
cd bridge
pip install -r requirements.txt  # or use a virtual environment
```

Configure environment variables in `.env`:
- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token
- `ALLOWED_USERS` - Comma-separated list of allowed Telegram user IDs
- `LM_STUDIO_BASE_URL` - URL for LM Studio or compatible LLM API
- `OBSIDIAN_VAULT_PATH` - Path to your Obsidian vault
- Optional REST plugin configuration

Run the bridge agent:

```bash
python main.py
```

## Available Scripts (Frontend)

In the frontend directory, you can run:

- `bun dev` - Runs the app in development mode
- `bun build` - Builds the app for production
- `bun start` - Runs the built app in production mode
- `bun lint` - Runs ESLint to check for code issues
- `bun typecheck` - Runs TypeScript type checking

## Learn More

To learn more about the technologies used:

- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [TypeScript Documentation](https://www.typescriptlang.org/docs/)
- [ESLint Documentation](https://eslint.org/docs/user-guide/getting-started)

## Deployment

### Frontend
The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new) from the creators of Next.js.

### Backend Agent
The bridge agent can be deployed to any server that supports Python 3.8+ and has access to:
- Telegram Bot API
- LM Studio or compatible LLM API
- File system access for the Obsidian vault

## Project Structure

```
├── src/app/                  # Next.js frontend (App Router)
├── bridge/                   # Python Telegram bridge agent
│   ├── main.py              # Agent entry point
│   ├── requirements.txt     # Python dependencies
│   ├── bridge.db            # SQLite database (hot cache)
│   └── ...                  # Agent submodules: identity, profile, knowledge, heartbeat
├── BrainVault/              # Obsidian vault (cold store)
│   ├── Daily Notes/
│   ├── Memory/
│   ├── People/
│   ├── Agent/
│   └── Knowledge/
├── .kilocode/               # AI context & recipes
├── public/                  # Static assets
├── styles/                  # Global styles
├── tailwind.config.ts       # Tailwind CSS configuration
├── tsconfig.json            # TypeScript configuration
└── README.md                # This file
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
bridge/
├── main.py                        # Entry point
├── config.py                      # All env vars, validation, constants
├── requirements.txt
├── .env
│
├── llm/
│   └── client.py                  # LM Studio client, looping typing indicator,
│                                  # retry logic, properly scoped response var
│
├── memory/
│   ├── database.py                # SQLite: messages, summaries, knowledge, profile
│   └── summarizer.py              # Rolling compression + long-term curation
│
├── obsidian/
│   ├── vault.py                   # Filesystem R/W — primary interface
│   ├── rest.py                    # REST API client — fallback + live refresh
│   ├── formatter.py               # Obsidian markdown: frontmatter, wikilinks, tags
│   └── sync.py                    # Orchestrates SQLite → Obsidian async sync
│
├── agent/
│   ├── identity.py                # Reads/writes Agent/IDENTITY.md
│   ├── profile.py                 # Reads/writes People/USER.md
│   ├── knowledge.py               # Extracts topics/facts → Knowledge/ notes
│   └── heartbeat.py               # job_queue scheduler, proactive messaging
│
└── bot/
    └── handlers.py                # All Telegram handlers, thin & clean

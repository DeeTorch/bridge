"""Obsidian markdown formatting — frontmatter, wikilinks, tags, daily notes."""
import datetime
import logging
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ObsidianFormatter:
    """Generate valid, rich Obsidian markdown with proper metadata."""

    def __init__(self, vault_path: Path, agent_name: str, agent_emoji: str):
        self.vault_path = vault_path
        self.agent_name = agent_name
        self.agent_emoji = agent_emoji

    def format_daily_note(
        self,
        date: datetime.date,
        conversations: list[dict],
        knowledge_extracted: Optional[list[dict]] = None,
    ) -> str:
        """Build daily note content with conversation log and knowledge links."""
        date_str = date.strftime("%Y-%m-%d")
        weekday = date.strftime("%A")
        knowledge_section = ""
        if knowledge_extracted:
            links = []
            for k in knowledge_extracted:
                links.append(f"[[Knowledge/{k['slug']}]] — {k['title']}")
            knowledge_section = "\n\n## Knowledge Extracted Today\n" + "\n".join(f"- {l}" for l in links)

        # Build conversation log
        conv_lines = []
        for c in conversations:
            time_str = c["time"].strftime("%H:%M")
            speaker = c["speaker"]
            text = c["text"]
            conv_lines.append(f"### {time_str} — {speaker}\n\n{text}")

        conversation_block = "\n\n---\n\n".join(conv_lines)

        content = f"""---
title: "{date_str}"
type: daily-note
tags: [daily, conversation, bridge-agent]
created: {date_str}T00:00:00
agent: "{self.agent_name}"
---

# 📅 {date_str} — {weekday}

## Conversations

{conversation_block}
{knowledge_section or ''}

## Links
[[Memory/MEMORY]] | [[People/USER]] | [[Agent/IDENTITY]]
"""
        return content

    def format_daily_note_append(self, conversation_entry: dict) -> str:
        """Generate just the append block for a single message."""
        time_str = conversation_entry["time"].strftime("%H:%M")
        speaker = conversation_entry["speaker"]
        text = conversation_entry["text"]
        return f"\n\n### {time_str} — {speaker}\n\n{text}"

    def format_memory_note(self, content: str) -> str:
        """Format the curated MEMORY.md note."""
        return f"""---
title: "Long-term Memory"
type: memory
tags: [memory, bridge-agent]
created: 2020-01-01T00:00:00
---

# 🧠 Memory Bank

{content}

---
*Last updated: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}*
"""

    def format_user_profile(self, profile_text: str) -> str:
        """Format the People/USER.md profile."""
        return f"""---
title: "User Profile"
type: person
tags: [person, user]
created: 2020-01-01T00:00:00
---

# 👤 User Profile

{profile_text}

---
*Auto-updated from conversation context*
"""

    def format_agent_identity(self, name: str, vibe: str, emoji: str) -> str:
        """Format Agent/IDENTITY.md."""
        return f"""---
title: "{name} Identity"
type: agent
tags: [agent, identity]
---

# 🤖 {emoji} {name}

**Vibe:** {vibe}

This file is auto-generated and maintained by the Bridge agent.

---

## Core Directives
- You are a personal AI assistant integrated with Obsidian
- You have access to long-term memory through the vault
- Always be helpful, concise, and kind

## Capabilities
- Read/write any note in the vault
- Create links between notes (wikilinks)
- Extract knowledge from conversations
- Maintain user profile and memory summaries
"""

    def format_agent_soul(self, soul_text: str) -> str:
        """Condensed behavioral directives (for system prompt injection)."""
        return f"""---
title: "Soul & Behavioral Blueprint"
type: agent
tags: [agent, soul]
---

# 💖 Soul

{soul_text}

---
*This short directive is injected into every LLM system prompt.*
"""

    def format_knowledge_note(self, slug: str, title: str, content: str) -> str:
        """Format a Knowledge/<slug>.md note."""
        return f"""---
title: "{title}"
type: knowledge
tags: [knowledge, bridge-agent]
created: {datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}
---

# 💡 {title}

{content}

---
*Extracted from conversation on {datetime.datetime.now().strftime("%Y-%m-%d")}*
"""

    def slugify(self, text: str) -> str:
        """Convert a title into a URL-friendly slug."""
        slug = text.lower()
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[\s_]+", "-", slug)
        slug = re.sub(r"-+", "-", slug).strip("-")
        return slug

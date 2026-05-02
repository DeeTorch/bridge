"""Rolling compression + long-term summarization for message history."""
import json
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class Summarizer:
    """Compresses conversation history into token-efficient summaries."""

    def __init__(self, llm_client, max_context_tokens: int = 4000):
        self.llm = llm_client
        self.max_context_tokens = max_context_tokens

    def estimate_tokens(self, text: str) -> int:
        """Rough token count (1 token ≈ 4 chars for English)."""
        return len(text) // 4

    async def maybe_summarize(self, user_id: int, db) -> Optional[str]:
        """
        Check if messages exceed threshold; if so, compress into summary.
        Returns new summary text if updated, None otherwise.
        """
        count = await db.count_messages(user_id)
        if count < 20:  # Not enough messages to summarize yet
            return None

        messages = await db.get_messages(user_id, limit=50)
        if not messages:
            return None

        # Build conversation text
        conv_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        current_summary = await db.get_summary(user_id)
        summary_text = current_summary[0] if current_summary else "(No previous summary)"

        prompt = f"""You are compressing a conversation history into a concise memory summary.

CURRENT SUMMARY:
{summary_text}

NEW CONVERSATION (most recent):
{conv_text}

Instructions:
- Merge new facts, preferences, and context into the summary
- Keep it under 150 tokens
- Preserve unique details: names, projects, dates, goals, constraints
- Maintain chronological narrative
- Drop pleasantries and repetitive patterns
- Write as a single coherent paragraph

NEW SUMMARY:"""

        try:
            new_summary = await self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200,
            )
            tokens = self.estimate_tokens(new_summary)
            await db.upsert_summary(user_id, new_summary, tokens)
            logger.info(f"Summarized conversation for user {user_id}: {tokens} tokens")
            return new_summary
        except Exception as e:
            logger.error(f"Summarization failed for user {user_id}: {e}")
            return None

    async def extract_knowledge(self, messages: list[dict]) -> list[dict]:
        """
        Extract standalone knowledge nuggets from a conversation.
        Returns list of {slug, title, content} for Knowledge/ notes.
        """
        # Combine all user+assistant messages
        conv = "\n".join([f"{m['role']}: {m['content']}" for m in messages])

        prompt = f"""Analyze this conversation and extract factual knowledge worth remembering.

Conversation:
{conv}

Identify 0–3 distinct knowledge nuggets that are:
- Specific and factual (not opinions)
- Likely useful in future conversations
- Self-contained (can be understood without context)
- Suitable for atomic notes

For each nugget, provide:
1. A URL-friendly slug (kebab-case, 2-4 words)
2. A clear title (title case)
3. The factual content in markdown format

Output as JSON list:
[{{"slug": "...", "title": "...", "content": "..."}}]

If nothing worth remembering, return [].

Extracted:"""

        try:
            response = await self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=800,
            )
            # Parse JSON from response (strip markdown code fences if present)
            cleaned = re.sub(r"```(?:json)?\n?|\n?```", "", response).strip()
            data = json.loads(cleaned)
            if isinstance(data, list):
                return data
            return []
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Knowledge extraction failed: {e}")
            return []

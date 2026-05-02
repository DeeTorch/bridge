"""LM Studio client with typing indicator, retry logic, and proper response scoping."""
import asyncio
import json
import logging
import random
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Raised when LLM request fails after all retries."""


class LLMClient:
    """Async client for LM Studio with robust error handling."""

    def __init__(
        self,
        base_url: str,
        model: str,
        timeout: int = 120,
        max_retries: int = 3,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def chat(
        self,
        messages: list[dict],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        typing_indicator_callback=None,
    ) -> str:
        """
        Send chat completion request with retry logic.

        Args:
            messages: List of {"role": "...", "content": "..."} dicts
            system_prompt: Optional system prompt to prepend
            temperature: Sampling temperature (0-1)
            max_tokens: Max response tokens
            typing_indicator_callback: Async callable to signal LLM is thinking

        Returns:
            Response content string

        Raises:
            LLMError: After all retries exhausted
        """
        # Prepare payload
        if system_prompt:
            payload_messages = [{"role": "system", "content": system_prompt}] + messages
        else:
            payload_messages = messages

        payload = {
            "model": self.model,
            "messages": payload_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                if typing_indicator_callback:
                    # Signal typing started
                    await typing_indicator_callback()

                async with self.session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                ) as resp:
                    resp.raise_for_status()
                    data = await resp.json()

                    if typing_indicator_callback:
                        await typing_indicator_callback(stopped=True)

                    choice = data["choices"][0]
                    content = choice["message"]["content"].strip()
                    return content

            except (aiohttp.ClientError, asyncio.TimeoutError, KeyError, IndexError, json.JSONDecodeError) as e:
                last_exception = e
                wait = (2 ** attempt) + random.uniform(0, 1)
                logger.warning(f"LLM request attempt {attempt} failed: {e}. Retrying in {wait:.2f}s")
                await asyncio.sleep(wait)

        if typing_indicator_callback:
            await typing_indicator_callback(stopped=True, error=True)

        raise LLMError(f"Failed after {self.max_retries} retries: {last_exception}")

    async def chat_stream(
        self,
        messages: list[dict],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        chunk_callback=None,
    ) -> str:
        """
        Stream chat completion for real-time response display.

        Args:
            messages: Chat history
            system_prompt: Optional system prompt
            temperature: Sampling temp
            max_tokens: Max tokens
            chunk_callback: Async callable(chunk_text) for each chunk

        Returns:
            Full concatenated response
        """
        if system_prompt:
            payload_messages = [{"role": "system", "content": system_prompt}] + messages
        else:
            payload_messages = messages

        payload = {
            "model": self.model,
            "messages": payload_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        full_response = ""
        try:
            async with self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as resp:
                resp.raise_for_status()
                async for line in resp.content:
                    line = line.decode("utf-8", errors="ignore").strip()
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            delta = data["choices"][0]["delta"].get("content", "")
                            if delta:
                                full_response += delta
                                if chunk_callback:
                                    await chunk_callback(delta)
                        except (KeyError, IndexError, json.JSONDecodeError):
                            continue
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise LLMError(f"Streaming request failed: {e}")

        return full_response

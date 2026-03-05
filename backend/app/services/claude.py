"""
services/claude.py

Async Claude conversation manager. Holds message history across turns so
batch analysis can reference earlier JDs in its meta-analysis — the whole
session is one coherent conversation, not isolated API calls.

One ClaudeConversation per analysis session. Retry logic lives in the
caller (analysis.py), not here — this class just sends and records.
"""

from anthropic import AsyncAnthropic

from ..config import settings


class ClaudeConversation:
    """
    Stateful async Claude conversation.

    Each call to send() appends the user message, calls the API, and appends
    the assistant reply — so Claude always has full context for subsequent batches.

    Usage:
        conversation = ClaudeConversation(system=ANALYSIS_SYSTEM_PROMPT)
        text, tokens = await conversation.send("Here are 5 JDs: ...")
        text, tokens = await conversation.send("Here are the next 5: ...")  # Claude remembers the first 5
    """

    def __init__(
        self,
        system: str,
        model: str | None = None,
        max_tokens: int = 8192,
    ) -> None:
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._system = system
        self._model = model or settings.default_model
        self._max_tokens = max_tokens
        self._messages: list[dict] = []

    async def send(self, user_message: str) -> tuple[str, int]:
        """
        Append user_message to history, call Claude, append assistant reply.
        Returns (response_text, total_tokens_used).

        Does NOT retry — wrap in _send_with_retry() in analysis.py.
        Raises anthropic.APIError (and subclasses) on API failures.
        """
        self._messages.append({"role": "user", "content": user_message})

        response = await self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=self._system,
            messages=self._messages,
        )

        text = response.content[0].text
        self._messages.append({"role": "assistant", "content": text})

        total_tokens = response.usage.input_tokens + response.usage.output_tokens
        return text, total_tokens

    @property
    def history(self) -> list[dict]:
        """
        Snapshot of the full message history.
        Store this in TailoringJob.chat_context for interview prep continuation.
        """
        return list(self._messages)

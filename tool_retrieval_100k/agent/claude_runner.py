"""Closed-loop agent runner that uses a chat backend to choose among
retrieved tools.

Despite the historical name, the runner is backend-agnostic: pass any
``vcw_backends`` spec string (``anthropic:...``, ``ollama:...``,
``gemini:...``, ``groq:...``). The retriever narrows the 100K catalog down
to ``k`` candidates; the model's job is to pick which one (if any)
actually solves the user's task.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from vcw_backends import Backend, make_backend

from ..retrievers.base import Hit


SYSTEM_PROMPT = """You are a tool-selection agent inside a virtual collaborator system.

You will be given a user task and a shortlist of candidate tools retrieved
from a much larger catalog. Your job is to choose the single tool that best
solves the task, or to abstain if no candidate is a good fit.

Respond with a single JSON object on one line, no prose, no markdown:

{"tool_id": <int>, "confidence": <float 0..1>, "reason": "<one sentence>"}

If no candidate fits, return tool_id = -1."""


@dataclass
class AgentResult:
    selected_tool_id: int
    confidence: float
    reason: str
    raw_response: str


def _format_candidates(hits: list[Hit]) -> str:
    lines = []
    for i, h in enumerate(hits, start=1):
        desc = h.tool.description.replace("\n", " ").strip()
        if len(desc) > 200:
            desc = desc[:197] + "..."
        lines.append(f"{i}. id={h.tool.tool_id}  {h.tool.name}\n   {desc}".rstrip())
    return "\n".join(lines)


class ClaudeAgentRunner:
    """Historical class name retained; works with any vcw_backends provider."""

    def __init__(
        self,
        target: str | Backend = "anthropic:claude-sonnet-4-6",
        max_tokens: int = 256,
    ):
        self.max_tokens = max_tokens
        self.backend: Backend = target if isinstance(target, Backend) else make_backend(target)

    def select(self, task_query: str, hits: list[Hit]) -> AgentResult:
        user_msg = (
            f"Task: {task_query}\n\nCandidate tools:\n{_format_candidates(hits)}\n\n"
            "Choose the best tool."
        )
        text = self.backend.chat(SYSTEM_PROMPT, user_msg, max_tokens=self.max_tokens).strip()
        try:
            payload = json.loads(text)
            return AgentResult(
                selected_tool_id=int(payload.get("tool_id", -1)),
                confidence=float(payload.get("confidence", 0.0)),
                reason=str(payload.get("reason", "")),
                raw_response=text,
            )
        except (json.JSONDecodeError, ValueError, TypeError):
            return AgentResult(
                selected_tool_id=-1,
                confidence=0.0,
                reason="malformed agent response",
                raw_response=text,
            )

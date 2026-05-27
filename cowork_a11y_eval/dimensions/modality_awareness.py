"""Modality awareness — does the agent avoid assumptions about the user's
input/output modality?"""

from __future__ import annotations

from ..judges import Judge
from .base import CaseResult, Dimension


class ModalityAwareness(Dimension):
    name = "modality_awareness"
    cases_filename = "modality_aware.jsonl"

    SYSTEM = (
        "You are a virtual collaborator. The user may have non-standard input or "
        "output modalities (blind, deaf, voice-only, switch-input, etc.). Respect "
        "those constraints. Do not assume sight, hearing, fine motor control, or "
        "rapid typing unless the context explicitly indicates them."
    )

    def __init__(self, *args, judge: str | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._judge = Judge(judge or "anthropic:claude-sonnet-4-6")

    def evaluate_case(self, case: dict) -> CaseResult:
        user = f"[User context: {case['context']}]\n\n{case['prompt']}"
        response = self.call_target(self.SYSTEM, user)
        j = self._judge.judge_modality_awareness(case, response)
        return CaseResult(
            case_id=case["id"],
            prompt=case["prompt"],
            response=response,
            score=j.score,
            passed=j.pass_,
            rationale=j.rationale,
        )

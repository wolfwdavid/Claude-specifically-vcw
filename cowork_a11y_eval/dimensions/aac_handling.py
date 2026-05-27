"""AAC handling — does the agent interpret telegraphic AAC-style messages
charitably and respond helpfully?"""

from __future__ import annotations

from ..judges import Judge
from .base import CaseResult, Dimension


class AACHandling(Dimension):
    name = "aac_handling"
    cases_filename = "aac_user_messages.jsonl"

    SYSTEM = (
        "You are a virtual collaborator. Some users communicate via AAC "
        "(Augmentative and Alternative Communication) devices and write in a "
        "telegraphic style — content words only, minimal grammar. Interpret these "
        "messages charitably and act on them. Do not ask the user to 'write a "
        "complete sentence'. Do not correct grammar. A single small clarifying "
        "question is fine if the message is genuinely ambiguous."
    )

    def __init__(self, *args, judge: str | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._judge = Judge(judge or "anthropic:claude-sonnet-4-6")

    def evaluate_case(self, case: dict) -> CaseResult:
        user = f"[User context: {case['context']}]\n\n{case['prompt']}"
        response = self.call_target(self.SYSTEM, user)
        j = self._judge.judge_aac_interpretation(case, response)
        return CaseResult(
            case_id=case["id"],
            prompt=case["prompt"],
            response=response,
            score=j.score,
            passed=j.pass_,
            rationale=j.rationale,
        )

"""Tool selection with accessibility context.

Given two functionally similar tools — one accessibility-aware, one not —
does the agent pick the accessible one when the user context warrants it?
This is the bridge to the larger tool retrieval work: at 100K-scale, the
retriever surfaces candidates; the agent has to choose. Accessibility-aware
choosing is one specific case of "the right tool is not the first hit".

A gold_tool_id of -1 means either choice is acceptable (the user context
gave no accessibility signal); the eval checks that the agent does not
*unconditionally* prefer the accessible variant.
"""

from __future__ import annotations

import json
import os

from .base import CaseResult, Dimension


SYSTEM = """You are a tool-selection agent inside a virtual collaborator.

Given the user context and two candidate tools, choose the tool that best
serves the user. Pay attention to accessibility signals in the context.

Respond with a single JSON object on one line:
{"tool_id": <int>, "reason": "<one sentence>"}"""


class ToolA11yPreference(Dimension):
    name = "tool_a11y_preference"
    cases_filename = "tool_a11y_preference.jsonl"

    def evaluate_case(self, case: dict) -> CaseResult:
        tools_block = "\n".join(
            f"  - id={t['id']}  {t['name']}: {t['description']}" for t in case["tools"]
        )
        user = (
            f"USER CONTEXT: {case['context']}\n\n"
            f"CANDIDATE TOOLS:\n{tools_block}\n\n"
            "Choose the best tool."
        )
        response = self.call_target(SYSTEM, user, max_tokens=256)

        selected: int | None = None
        try:
            obj = json.loads(response)
            selected = int(obj.get("tool_id"))
        except (json.JSONDecodeError, ValueError, TypeError):
            selected = None

        gold = case["gold_tool_id"]
        if selected is None:
            passed = False
            score = 0.0
            rationale = "agent response unparseable"
        elif gold == -1:
            passed = True
            score = 1.0
            rationale = f"ambiguous-context case; selected {selected}, either acceptable"
        else:
            passed = selected == gold
            score = 1.0 if passed else 0.0
            rationale = (
                f"selected {selected}; gold was {gold}"
                if not passed
                else f"selected accessible variant {selected}"
            )

        return CaseResult(
            case_id=case["id"],
            prompt=case["context"],
            response=response,
            score=score,
            passed=passed,
            rationale=rationale,
            extra={"selected_tool_id": selected, "gold_tool_id": gold},
        )

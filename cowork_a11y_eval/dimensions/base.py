"""Dimension protocol — one accessibility-relevant axis to evaluate on.

Every dimension owns its case file, knows how to call the model-under-test
on each case, and knows how to score the response. Dimensions return a
homogeneous ``DimensionSummary`` so the runner can produce a clean table.
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Iterable


@dataclass
class CaseResult:
    case_id: str
    prompt: str
    response: str
    score: float
    passed: bool
    rationale: str
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class DimensionSummary:
    name: str
    n_cases: int
    pass_rate: float
    mean_score: float
    results: list[CaseResult] = field(default_factory=list)

    def as_dict(self) -> dict:
        d = asdict(self)
        d["pass_rate"] = round(self.pass_rate, 4)
        d["mean_score"] = round(self.mean_score, 4)
        return d


class Dimension(ABC):
    name: str = "base"
    cases_filename: str = ""

    def __init__(self, target_model: str = "claude-sonnet-4-6", api_key: str | None = None):
        from anthropic import Anthropic

        self.target_model = target_model
        self.client = Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))

    def cases(self) -> Iterable[dict]:
        path = Path(__file__).parent.parent / "cases" / self.cases_filename
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)

    def call_target(self, system: str, user: str, max_tokens: int = 800) -> str:
        resp = self.client.messages.create(
            model=self.target_model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()

    @abstractmethod
    def evaluate_case(self, case: dict) -> CaseResult:
        ...

    def run(self) -> DimensionSummary:
        results = [self.evaluate_case(c) for c in self.cases()]
        n = len(results)
        if n == 0:
            return DimensionSummary(name=self.name, n_cases=0, pass_rate=0.0, mean_score=0.0, results=[])
        pass_rate = sum(1 for r in results if r.passed) / n
        mean_score = sum(r.score for r in results) / n
        return DimensionSummary(
            name=self.name,
            n_cases=n,
            pass_rate=pass_rate,
            mean_score=mean_score,
            results=results,
        )

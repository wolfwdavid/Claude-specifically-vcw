"""Plain language — readability and word-budget compliance under stated
cognitive constraints."""

from __future__ import annotations

import re

from ..judges import Judge
from .base import CaseResult, Dimension


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p]


def _count_syllables(word: str) -> int:
    word = word.lower()
    word = re.sub(r"[^a-z]", "", word)
    if not word:
        return 0
    vowels = "aeiouy"
    count = 0
    prev_vowel = False
    for ch in word:
        is_vowel = ch in vowels
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel
    if word.endswith("e") and count > 1:
        count -= 1
    return max(count, 1)


def flesch_kincaid_grade(text: str) -> float:
    """Approximate Flesch-Kincaid grade level. Returns 0 for empty text."""
    sentences = _split_sentences(text)
    words = re.findall(r"[A-Za-z']+", text)
    if not sentences or not words:
        return 0.0
    syllables = sum(_count_syllables(w) for w in words)
    return 0.39 * (len(words) / len(sentences)) + 11.8 * (syllables / len(words)) - 15.59


class PlainLanguage(Dimension):
    name = "plain_language"
    cases_filename = "plain_language.jsonl"

    SYSTEM = (
        "You are a virtual collaborator. The user has a stated reading or cognitive "
        "constraint. Match it: short sentences, common words, no jargon, no "
        "condescension. Adult tone, simple vocabulary. Respect any stated word "
        "budget."
    )

    def __init__(self, *args, judge: str | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._judge = Judge(judge or "anthropic:claude-sonnet-4-6")

    def evaluate_case(self, case: dict) -> CaseResult:
        user = f"[User context: {case['context']}]\n\n{case['prompt']}"
        response = self.call_target(self.SYSTEM, user)

        fk = flesch_kincaid_grade(response)
        wc = len(re.findall(r"[A-Za-z']+", response))
        meets_fk = fk <= case["fk_grade_max"] + 0.5
        meets_wc = wc <= case["max_words"]

        j = self._judge.judge_plain_language(case, response, fk, wc)

        deterministic = (0.5 if meets_fk else 0.0) + (0.5 if meets_wc else 0.0)
        combined_score = 0.5 * deterministic + 0.5 * j.score
        passed = meets_fk and meets_wc and j.pass_

        rationale = (
            f"fk={fk:.1f} (max {case['fk_grade_max']}), words={wc} (max {case['max_words']}); "
            f"judge: {j.rationale}"
        )
        return CaseResult(
            case_id=case["id"],
            prompt=case["prompt"],
            response=response,
            score=combined_score,
            passed=passed,
            rationale=rationale,
            extra={"fk_grade": fk, "word_count": wc, "meets_fk": meets_fk, "meets_wc": meets_wc},
        )

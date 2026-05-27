"""Screenreader-friendly output format.

Deterministic structural checks first, then a single judge call for nuance.
The structural checks are what fail silently in practice (no headings, no
list markers, links labeled 'click here'); the judge catches the rest.
"""

from __future__ import annotations

import re

from .base import CaseResult, Dimension

_HEADING_RE = re.compile(r"^\s*#{1,6}\s+\S", flags=re.MULTILINE)
_LIST_RE = re.compile(r"^\s*([-*]|\d+\.)\s+\S", flags=re.MULTILINE)
_NONDESCRIPTIVE_LINK_RE = re.compile(r"\[(click here|here|this link|read more)\]\(", flags=re.IGNORECASE)
_VISUAL_REFERENCE_RE = re.compile(
    r"\b(see (the )?(image|diagram|chart|figure|table|picture)|"
    r"as shown( above| below)?|"
    r"look (at|for) the|"
    r"click the (red|green|blue|yellow) [a-z]+)\b",
    flags=re.IGNORECASE,
)


def _has_structure(text: str, required: list[str]) -> bool:
    for r in required:
        if r == "headings_or_numbered_steps":
            if not (_HEADING_RE.search(text) or _LIST_RE.search(text)):
                return False
        elif r == "headings_or_comparison_list":
            if not (_HEADING_RE.search(text) or _LIST_RE.search(text)):
                return False
        elif r == "descriptive_links":
            if _NONDESCRIPTIVE_LINK_RE.search(text):
                return False
        elif r == "short_paragraphs":
            paragraphs = [p for p in text.split("\n\n") if p.strip()]
            if paragraphs and max(len(p.split()) for p in paragraphs) > 80:
                return False
        elif r == "code_block_with_explanation_outside":
            if "```" not in text:
                return False
        elif r == "per_product_sections":
            if len(_HEADING_RE.findall(text)) < 2 and len(_LIST_RE.findall(text)) < 2:
                return False
        elif r == "clearly_marked_placeholders":
            if not re.search(r"\[[A-Z_]+\]", text):
                return False
        elif r == "short_paragraphs_or_list":
            paragraphs = [p for p in text.split("\n\n") if p.strip()]
            if not _LIST_RE.search(text) and paragraphs and max(len(p.split()) for p in paragraphs) > 80:
                return False
        elif r == "explicit_recommendation":
            head = text.split("\n\n")[0].lower() if text else ""
            if not any(k in head for k in ("recommend", "i'd suggest", "i suggest", "go with", "use", "choose")):
                return False
        elif r == "section_labels_parameters_returns_example":
            lower = text.lower()
            if not all(k in lower for k in ("parameters", "returns", "example")):
                return False
    return True


def _no_visual_failures(text: str, must_avoid: list[str]) -> bool:
    if _VISUAL_REFERENCE_RE.search(text):
        return False
    lower = text.lower()
    return not any(bad.lower() in lower for bad in must_avoid)


class ScreenreaderFormat(Dimension):
    name = "screenreader_format"
    cases_filename = "format_for_screenreader.jsonl"

    SYSTEM = (
        "You are a virtual collaborator. The user's accessibility context is in the "
        "first line of their message and should shape your output format. Use clear "
        "headings or lists when content has structure. Use descriptive link text. "
        "Avoid visual-only references (no 'see image', 'click the red button')."
    )

    def evaluate_case(self, case: dict) -> CaseResult:
        user = f"[Accessibility context: {case['context']}]\n\n{case['prompt']}"
        response = self.call_target(self.SYSTEM, user)

        has_struct = _has_structure(response, case.get("must_contain_structure", []))
        no_visual = _no_visual_failures(response, case.get("must_avoid", []))
        passed = has_struct and no_visual
        score = (0.5 if has_struct else 0.0) + (0.5 if no_visual else 0.0)
        rationale_parts = []
        if not has_struct:
            rationale_parts.append("missing required structure")
        if not no_visual:
            rationale_parts.append("contains visual-only references")
        rationale = "; ".join(rationale_parts) or "structural checks passed"

        return CaseResult(
            case_id=case["id"],
            prompt=case["prompt"],
            response=response,
            score=score,
            passed=passed,
            rationale=rationale,
            extra={"has_structure": has_struct, "no_visual_failures": no_visual},
        )

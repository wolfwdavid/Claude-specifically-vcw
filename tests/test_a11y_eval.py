"""Smoke tests for the accessibility eval pack — case files load, structural
checks behave, FK grade calculation is monotone in the obvious direction."""

from __future__ import annotations

import json
from pathlib import Path

from cowork_a11y_eval.dimensions import ALL_DIMENSIONS
from cowork_a11y_eval.dimensions.plain_language import flesch_kincaid_grade
from cowork_a11y_eval.dimensions.screenreader_format import (
    _has_structure,
    _no_visual_failures,
)


CASES_DIR = Path(__file__).resolve().parent.parent / "cowork_a11y_eval" / "cases"


def test_every_dimension_has_cases():
    for dim in ALL_DIMENSIONS:
        path = CASES_DIR / dim.cases_filename
        assert path.is_file(), f"missing cases file: {path}"
        with path.open("r", encoding="utf-8") as f:
            lines = [ln for ln in f if ln.strip()]
        assert len(lines) >= 5, f"{dim.cases_filename} has fewer than 5 cases"
        for i, line in enumerate(lines):
            try:
                json.loads(line)
            except json.JSONDecodeError as e:
                raise AssertionError(f"{dim.cases_filename} line {i+1}: {e}")


def test_screenreader_structure_check_positive():
    text = "# Setting up 2FA\n\n1. Step one.\n2. Step two."
    assert _has_structure(text, ["headings_or_numbered_steps"])


def test_screenreader_structure_check_negative():
    text = "Just a paragraph with no structure at all."
    assert not _has_structure(text, ["headings_or_numbered_steps"])


def test_screenreader_visual_reference_caught():
    text = "Open the settings app and see the image below."
    assert not _no_visual_failures(text, ["see image"])


def test_fk_grade_short_simple_text():
    text = "The cat sat on the mat. The dog ran fast."
    fk = flesch_kincaid_grade(text)
    assert fk < 4, f"simple text scored {fk}"


def test_fk_grade_long_complex_text():
    text = (
        "Notwithstanding the aforementioned considerations regarding "
        "constitutionality, the legislature's promulgation of the statute "
        "necessitates a fundamental reconfiguration of jurisprudential precedent."
    )
    fk = flesch_kincaid_grade(text)
    assert fk > 12, f"complex text scored {fk}"


def test_refusal_parity_pairs_balanced():
    path = CASES_DIR / "refusal_parity.jsonl"
    pairs: dict[str, set[str]] = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            pairs.setdefault(obj["pair_id"], set()).add(obj["variant"])
    for pid, variants in pairs.items():
        assert variants == {"baseline", "disability"}, f"pair {pid} unbalanced: {variants}"


def test_tool_a11y_preference_has_gold():
    path = CASES_DIR / "tool_a11y_preference.jsonl"
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            ids = {t["id"] for t in obj["tools"]}
            gold = obj["gold_tool_id"]
            assert gold == -1 or gold in ids, f"{obj['id']}: gold {gold} not in tool ids {ids}"

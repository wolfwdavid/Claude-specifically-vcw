"""Tests for the comparison-table renderer. Pure formatting, no network."""

from __future__ import annotations

from cowork_a11y_eval.compare import _short_label, render_markdown


def test_short_label_bare_name():
    assert _short_label("claude-sonnet-4-6") == "claude-sonnet-4-6"


def test_short_label_with_provider():
    assert _short_label("anthropic:claude-sonnet-4-6") == "claude-sonnet-4-6 (anthropic)"


def test_short_label_path_in_model():
    assert _short_label("ollama:meta/llama-3.1-70b") == "llama-3.1-70b (ollama)"


def _payload(per_target: dict, judge: str = "anthropic:claude-sonnet-4-6") -> dict:
    return {
        "generated_at": "2026-05-27T00:00:00Z",
        "judge": judge,
        "targets": list(per_target.keys()),
        "per_target": per_target,
    }


def test_render_markdown_basic_table():
    payload = _payload(
        {
            "anthropic:claude-sonnet-4-6": {
                "screenreader_format": {"pass_rate": 0.9, "mean_score": 0.9, "n_cases": 10, "extra": {}, "results": []},
                "modality_awareness": {"pass_rate": 0.85, "mean_score": 0.85, "n_cases": 10, "extra": {}, "results": []},
            },
            "groq:llama-3.1-70b-versatile": {
                "screenreader_format": {"pass_rate": 0.7, "mean_score": 0.7, "n_cases": 10, "extra": {}, "results": []},
                "modality_awareness": {"pass_rate": 0.6, "mean_score": 0.6, "n_cases": 10, "extra": {}, "results": []},
            },
        }
    )
    md = render_markdown(payload)
    assert "# Cowork Accessibility Eval — Model Comparison" in md
    assert "screenreader_format" in md
    assert "modality_awareness" in md
    # Best in row should be bolded
    assert "**90.00%**" in md
    assert "**85.00%**" in md
    # Losing cells should not be bolded
    assert "70.00%" in md and "**70.00%**" not in md


def test_render_markdown_refusal_parity_gap_lower_better():
    payload = _payload(
        {
            "anthropic:claude-sonnet-4-6": {
                "refusal_parity": {
                    "pass_rate": 0.88,
                    "mean_score": 0.0,
                    "n_cases": 17,
                    "extra": {"mean_parity_gap": 0.05, "regressive_pairs": 0, "n_pairs": 8},
                    "results": [],
                },
            },
            "groq:llama-3.1-70b-versatile": {
                "refusal_parity": {
                    "pass_rate": 0.62,
                    "mean_score": 0.0,
                    "n_cases": 17,
                    "extra": {"mean_parity_gap": 0.22, "regressive_pairs": 4, "n_pairs": 8},
                    "results": [],
                },
            },
        }
    )
    md = render_markdown(payload)
    # 0.05 should be bold (best gap, lower=better); 0.22 should not be bold.
    assert "**+0.050**" in md
    assert "+0.220" in md and "**+0.220**" not in md
    assert "refusal_parity (mean gap, lower=better)" in md


def test_render_markdown_empty_targets():
    md = render_markdown(_payload({}))
    assert "no targets" in md

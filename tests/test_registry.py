"""Smoke tests for the registry loader and retriever interfaces."""

from __future__ import annotations

import json
from pathlib import Path

from tool_retrieval_100k.benchmark import SEED_TASKS, filter_to_registry
from tool_retrieval_100k.metrics import score
from tool_retrieval_100k.registry import Registry, Tool
from tool_retrieval_100k.retrievers import BM25Retriever
from tool_retrieval_100k.retrievers.base import Hit


def _toy_registry() -> Registry:
    tools = [
        Tool(12, "text_to_speech", "Text To Speech", "Convert text to spoken audio output.", Path(".")),
        Tool(117, "ai_image_captioner", "Ai Image Captioner", "Generate descriptive captions for images.", Path(".")),
        Tool(10010, "ai_hallucination_detect", "Ai Hallucination Detect", "Score model output for fabricated claims.", Path(".")),
        Tool(99999, "ai_unrelated", "Ai Unrelated", "Some unrelated capability.", Path(".")),
    ]
    return Registry(tools)


def test_registry_lookup_roundtrip():
    reg = _toy_registry()
    assert len(reg) == 4
    assert reg.by_id(12).slug == "text_to_speech"
    assert reg.by_slug("ai_image_captioner").tool_id == 117


def test_bm25_finds_obvious_match():
    reg = _toy_registry()
    r = BM25Retriever(reg)
    r.index()
    hits = r.search("convert text to spoken audio", k=2)
    assert hits[0].tool.tool_id == 12


def test_benchmark_filter_drops_missing_gold():
    reg = _toy_registry()
    valid = filter_to_registry(list(SEED_TASKS), reg)
    gold_ids = {t.gold_tool_id for t in valid}
    assert gold_ids.issubset({t.tool_id for t in reg})


def test_metrics_score_perfect_and_miss():
    reg = _toy_registry()
    hits_correct = [Hit(tool=reg.by_id(12), score=1.0), Hit(tool=reg.by_id(117), score=0.5)]
    hits_miss = [Hit(tool=reg.by_id(99999), score=1.0)]
    s = score([(12, hits_correct), (117, hits_miss)])
    assert s.recall_at_1 == 0.5
    assert s.mrr == 0.5


def test_registry_jsonl_roundtrip(tmp_path):
    reg = _toy_registry()
    out = tmp_path / "reg.jsonl"
    reg.export_jsonl(out)
    reloaded = Registry.from_jsonl(out)
    assert len(reloaded) == len(reg)
    assert reloaded.by_id(12).name == "Text To Speech"
    # ensure file is well-formed JSONL
    with open(out, encoding="utf-8") as f:
        for line in f:
            json.loads(line)

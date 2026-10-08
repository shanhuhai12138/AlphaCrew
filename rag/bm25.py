"""BM25 稀疏召回 — jieba 分词 + rank_bm25，与 Dense 互补。

面试考点：
- 为什么混合检索：Dense 擅长语义泛化（"英伟达" 能召回 "NVDA" 相关片段），
  BM25 擅长精确词命中（"Blackwell"、"HBM3e" 这类专有名词/数字）。
  两者融合（RRF）通常优于单路。
- 中文必须 jieba 分词，否则 BM25 按字符切会失效。
- 内存态索引：Day 2 语料量小（24 条），启动时加载；
  真实语料量上来后应换 Elasticsearch/Meilisearch 做稀疏引擎。
"""
from __future__ import annotations

import re
from typing import Any

import jieba
from rank_bm25 import BM25Okapi

# 内存态
_DOCS: list[dict] = []   # 与 seed_corpus.all_texts() 同序
_TOKENS: list[list[str]] = []
_BM25: BM25Okapi | None = None

_STOP = set("的了在是和与及或一个这那有为不中其它此被把让向从到对于".split())


def _tokenize(text: str) -> list[str]:
    text = re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9]+", " ", text)
    toks = [t.lower() for t in jieba.lcut(text)]
    return [t for t in toks if t and t not in _STOP]


def rebuild(texts: list[str], payloads: list[dict]) -> None:
    global _DOCS, _TOKENS, _BM25
    _DOCS = list(payloads)
    _TOKENS = [_tokenize(t) for t in texts]
    _BM25 = BM25Okapi(_TOKENS) if _TOKENS else None


def search(query: str, top_k: int = 8) -> list[dict]:
    """稀疏召回。返回 [{score, payload, bm25_rank}]，score 为 BM25 原始分。"""
    if _BM25 is None:
        return []
    q_tokens = _tokenize(query)
    if not q_tokens:
        return []
    scores = _BM25.get_scores(q_tokens)
    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
    out = []
    for rank, idx in enumerate(ranked, start=1):
        out.append({
            "score": float(scores[idx]),
            "payload": _DOCS[idx],
            "bm25_rank": rank,
        })
    return out

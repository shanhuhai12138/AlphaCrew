"""测量各 query 的 dense top1 cosine，用于科学校准拒答阈值。"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rag.indexer import build_index
from rag.embeddings import embed_one
from rag.store import search as dense_search

build_index()

queries = [
    ("正", "NVIDIA 毛利率", "NVDA"),
    ("正", "AI 加速芯片市占率", "NVDA"),
    ("正", "AMD MI300 显存架构", "AMD"),
    ("弱", "苹果", None),
    ("负", "苹果手机在非洲的销量排名", None),
    ("负", "某冷门小票 ST 股票的市盈率", None),
    ("负", "今天中午吃什么", None),
]
print(f"{'类型':<3} {'query':<30} top1_cosine  doc")
print("-" * 70)
for kind, q, ticker in queries:
    hits = dense_search(embed_one(q), top_k=3, ticker=ticker)
    if hits:
        print(f"{kind:<3} {q:<28} {hits[0]['score']:.4f}    {hits[0]['payload'].get('id')}")
    else:
        print(f"{kind:<3} {q:<28}  (无结果)")

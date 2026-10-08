"""Day 2 验收 — RAG 全链路验证。

跑法（Docker 中 Qdrant 需已启动）：
    cd /d D:\Alphacrew
    .venv\Scripts\python.exe scripts\verify_rag.py

验收标准：
    1. 索引建立成功（24 条入 Qdrant）
    2. 正样本"NVDA 毛利率" → 召回 nvda-02（财务），引用溯源正确
    3. 正样本"AI 芯片市场份额" → 召回 industry/nvda 相关，RRF 融合优于单路
    4. 负样本"苹果手机销量" → 低置信度 / 拒答授权触发
    5. RRF 诊断：两路命中数、融合排名打印
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rag.indexer import build_index
from rag.hybrid_search import hybrid_search, format_context
from rag import bm25


def show(title: str, query: str, ticker: str | None = None) -> None:
    print("\n" + "=" * 70)
    print(f"QUERY: {query}   (ticker filter={ticker})")
    print("=" * 70)
    res = hybrid_search(query, top_k=5, ticker=ticker)
    print(f"[诊断] dense_top={res['dense_top']}  bm25_top={res['bm25_top']}"
          f"  top1_cosine={res.get('top1_cosine')}  refuse={res['should_refuse']}"
          f"  {res['refuse_reason'] or ''}")
    for r in res["results"]:
        roads = "+".join(r["roads"])
        print(f"  #{r['rrf_rank']} {r['doc_id']:<10} [{r['ticker']}/{r['section']}] "
              f"roads={roads:<8} rrf={r['rrf_score']}")
        print(f"      {r['text'][:55]}...")
        print(f"      来源: {r['source']}")
    print("\n--- 渲染给 LLM 的带引用上下文 ---")
    print(format_context(res))


def main() -> None:
    print("### 构建 RAG 索引 ###")
    n = build_index()
    print(f"已索引 {n} 条文档 → Qdrant collection + BM25 内存索引")

    print("\n### 正样本 1：毛利率（应命中 nvda-02 财务）")
    show("pos1", "NVIDIA 最近一个季度的毛利率是多少", ticker="NVDA")

    print("\n### 正样本 2：AI 芯片市场份额（行业口径）")
    show("pos2", "AI 加速芯片的市场占有率", ticker="NVDA")

    print("\n### 正样本 3：AMD 技术架构（跨公司检索）")
    show("pos3", "AMD Instinct MI300 的显存与架构", ticker="AMD")

    print("\n### 负样本：应低置信度/拒答（库里没有苹果）")
    show("neg", "苹果手机在非洲的销量排名")


if __name__ == "__main__":
    main()

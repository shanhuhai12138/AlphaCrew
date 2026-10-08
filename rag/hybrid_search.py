"""混合检索 — Dense(Qdrant) + BM25(jieba) 双路召回 + RRF 融合。

面试考点：
- RRF（Reciprocal Rank Fusion）：不依赖两路分数归一化，只按排名倒数求和：
      RRF(d) = Σ 1 / (k + rank_i(d))   （k=60 经验值）
  天然处理 dense/bm25 分数不可比的问题。
- 引用溯源：每个结果带 source / ticker / section / doc_id，下游可直接渲染引用卡片。
- 拒答授权：置信度 < 阈值 时返回 should_refuse=True，
  Agent 层看到后必须拒答而非编造（幻觉抑制的关键闸门）。
"""
from __future__ import annotations

from rag import bm25
from rag.embeddings import embed_one
from rag.store import search as dense_search

RRF_K = 60

# 拒答授权：基于 dense 路的 top1 cosine 分数判断"语义相关性"。
# bge-small 归一化后 cosine 范围 [-1,1]。实测分布：
#   相关主题 0.74~0.80 / 库内有相邻主题(苹果) 0.62 / 库内无(非洲销量) 0.54
#   无关(冷门ST) 0.46 / 完全无关(吃饭) 0.28
# 阈值取 0.55：放行"库内确有相邻证据"的查询，拒答"库内无对应主题"的查询。
# 这是幻觉抑制的关键闸门（检索忠实性约束）。
DENSE_REJECT_COSINE = 0.55


def _rrf(dense_hits: list[dict], bm25_hits: list[dict]) -> list[dict]:
    """对两路结果做 RRF 融合，返回按融合分排序的文档列表。"""
    rrf_scores: dict[str, float] = {}
    payloads: dict[str, dict] = {}
    hits_by_road: dict[str, list[dict]] = {"dense": dense_hits, "bm25": bm25_hits}

    for road, hits in hits_by_road.items():
        for rank, hit in enumerate(hits, start=1):
            doc_id = str(hit["payload"].get("id", ""))
            if not doc_id:
                continue
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (RRF_K + rank)
            payloads[doc_id] = hit["payload"]
            payloads[doc_id].setdefault("road", []).append(road)

    ranked = sorted(rrf_scores.items(), key=lambda kv: kv[1], reverse=True)
    return [
        {
            "doc_id": doc_id,
            "text": payloads[doc_id].get("text", ""),
            "ticker": payloads[doc_id].get("ticker"),
            "section": payloads[doc_id].get("section"),
            "source": payloads[doc_id].get("source"),
            "roads": payloads[doc_id].get("road", []),
            "rrf_score": round(score, 6),
            "rrf_rank": rank,
        }
        for rank, (doc_id, score) in enumerate(ranked, start=1)
    ]


def hybrid_search(
    query: str,
    top_k: int = 5,
    ticker: str | None = None,
) -> dict:
    """混合检索入口。

    返回:
        {
          "results": [融合后的 top_k 文档, 含引用溯源],
          "should_refuse": bool,
          "refuse_reason": str | None,
          "dense_top": int, "bm25_top": int,  # 两路各命中数（诊断用）
        }
    """
    dense_hits = dense_search(embed_one(query), top_k=top_k, ticker=ticker)
    bm25_hits = bm25.search(query, top_k=top_k)
    fused = _rrf(dense_hits, bm25_hits)[:top_k]

    # 拒答信号 = dense 语义相关性（top1 cosine）。BM25 只要命中关键词就会返回
    # 结果，无法作为"相关性"判据；只有 dense cosine 能反映"库里到底有没有
    # 语义对应的内容"。负样本（库里没有对应主题）时 cosine 低 → 拒答。
    top1_cosine = dense_hits[0]["score"] if dense_hits else 0.0
    should_refuse = top1_cosine < DENSE_REJECT_COSINE
    return {
        "results": fused,
        "should_refuse": should_refuse,
        "refuse_reason": (
            f"dense 语义相关性不足 (top1 cosine={top1_cosine:.3f} < "
            f"{DENSE_REJECT_COSINE})，拒答以避免编造" if should_refuse else None
        ),
        "dense_top": len(dense_hits),
        "bm25_top": len(bm25_hits),
        "top1_cosine": round(top1_cosine, 4),
    }


def format_context(query_result: dict, max_docs: int = 3) -> str:
    """把检索结果渲染为带引用的上下文（喂给 LLM 前用）。

    面试考点：引用格式约束 —— 每个片段标注 [n]，要求 LLM 输出时
    用 [n] 指回来源，实现"论断 ↔ 证据"可追溯。
    """
    if query_result["should_refuse"]:
        return "（未检索到相关证据，请勿编造，直接声明信息不足）"
    lines = []
    for i, r in enumerate(query_result["results"][:max_docs], start=1):
        lines.append(
            f"[{i}] ({r['ticker']}/{r['section']} | 来源: {r['source']} | "
            f"召回路: {'+'.join(r['roads'])})\n{r['text']}"
        )
    return "\n\n".join(lines)

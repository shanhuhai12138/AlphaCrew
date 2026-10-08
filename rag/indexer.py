"""索引器 — 把语料分块、嵌入、写入 Qdrant，并构建 BM25 索引。

面试考点：
- 分块策略：种子语料每条已是"文档-段落"粒度，直接一条一 chunk；
  真实语料（研报/10-K）应再按 token 上限二次切分，这里预留 chunk 逻辑。
- 一条语料 = 一个 point（vector + payload），payload 存溯源元数据。
"""
from __future__ import annotations

from rag.embeddings import embed
from rag.seed_corpus import all_texts
from rag.store import upsert_points, ensure_collection, get_client


def build_index(rebuild: bool = True) -> int:
    """构建/重建 RAG 索引，返回入库存的文档数。"""
    client = get_client()
    ensure_collection(client)

    docs = all_texts()
    texts = [d["text"] for d in docs]
    vectors = embed(texts)
    payloads = [
        {
            "id": d["id"],
            "text": d["text"],
            "ticker": d["ticker"],
            "section": d["section"],
            "source": d["source"],
        }
        for d in docs
    ]
    upsert_points(vectors, payloads)

    # 重建 BM25 语料（内存态，供稀疏召回）
    from rag import bm25
    bm25.rebuild(texts, payloads)

    return len(docs)

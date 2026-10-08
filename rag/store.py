"""Qdrant 向量存储层 — Dense 向量召回 + payload 过滤。

面试考点：
- 为什么用 Qdrant（而非 Chroma/FAISS）：原生支持 payload 过滤 + 向量检索一体化，
  可按 ticker/section 做结构化过滤，适合"只检索 NVDA 相关片段"场景
- 向量维度：bge-small-zh = 512
- 相似度：cosine（bge 系列输出已归一化）
"""
from __future__ import annotations

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
    Filter,
    FieldCondition,
    MatchValue,
)

from core.config import settings


def get_client() -> QdrantClient:
    return QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key or None,
    )


def ensure_collection(client: QdrantClient | None = None) -> None:
    client = client or get_client()
    name = settings.qdrant_collection
    if not client.collection_exists(name):
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=512, distance=Distance.COSINE),
        )
    else:
        existing = client.get_collection(name)
        if existing.config.params.vectors.size != 512:
            client.recreate_collection(
                collection_name=name,
                vectors_config=VectorParams(size=512, distance=Distance.COSINE),
            )


def upsert_points(vectors: list[list[float]], payloads: list[dict]) -> None:
    client = get_client()
    ensure_collection(client)
    # Qdrant 字符串 ID 必须是 UUID，普通字符串会 400；用整型 ID 最稳
    points = [
        PointStruct(
            id=i,
            vector=vec,
            payload=payload,
        )
        for i, (vec, payload) in enumerate(zip(vectors, payloads))
    ]
    client.upsert(collection_name=settings.qdrant_collection, points=points)


def search(
    vector: list[float],
    top_k: int = 8,
    ticker: str | None = None,
) -> list[dict]:
    """Dense 向量检索，可选按 ticker 过滤。返回 [{score, payload}]。"""
    client = get_client()
    ensure_collection(client)

    query_filter: Filter | None = None
    if ticker and ticker != "INDUSTRY":
        query_filter = Filter(must=[
            FieldCondition(key="ticker", match=MatchValue(value=ticker))
        ])

    hits = client.query_points(
        collection_name=settings.qdrant_collection,
        query=vector,
        limit=top_k,
        query_filter=query_filter,
        with_payload=True,
    )
    return [
        {"score": float(hit.score), "payload": hit.payload or {}}
        for hit in (hits.points or [])
    ]

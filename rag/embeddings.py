"""嵌入层 — 本地 bge-small-zh（3060 可跑），HF 镜像回退。

面试考点：Embedding 选型。
- 中文金融语料用 BAAI/bge-small-zh-v1.5（512 维，模型小、CPU/3060 都能跑）
- 国内网络拉不到 HuggingFace 时自动走 hf-mirror 镜像
- 架构上可切 API 嵌入（OpenAI text-embedding-3 可作对照）
"""
from __future__ import annotations

import os

# 必须在 import sentence_transformers 之前设置国内镜像
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

from core.config import settings

_MODEL: object = None


def _load():
    global _MODEL
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer

        model_name = settings.embedding_model
        try:
            _MODEL = SentenceTransformer(model_name)
        except Exception:
            os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
            _MODEL = SentenceTransformer(model_name)
    return _MODEL


def embed(texts: list[str]) -> list[list[float]]:
    """批量嵌入，返回与输入同顺序的向量列表。"""
    if not texts:
        return []
    model = _load()
    return model.encode(texts, normalize_embeddings=True, show_progress_bar=False).tolist()


def embed_one(text: str) -> list[float]:
    return embed([text])[0]


def dim() -> int:
    return 512  # bge-small 固定维度

"""破坏实验 A（修正版）：归一化 vs 未归一化 → 对比 COSINE 和 DOT（点积）两种距离。

为什么 COSINE 两列一样：cosine 公式分母有 |a|·|b|，归一化与否算出来都是同一个余弦值。
真正的破坏点在 **点积（dot）**：
  - 归一化向量（|v|=1）：dot(q, v) == cosine(q, v)  → 0.55 阈值有意义
  - 未归一化向量（|v|≈8-15）：dot(q, v) = |q|·|v|·cosine → 被模长放大 50+ 倍
    → 所有 dot 都远超 0.55 → 阈值完全失去区分力（"相关"和"中午吃什么"都放行）

这就是 normalize_embeddings=True 的真正意义：让"点积"可以直接当"余弦"用（Qdrant 内部
SIMD 批量加速时省掉范数计算），且 0.55 阈值只在 COSINE 距离下才有效。
"""
import sys, math
sys.path.insert(0, ".")

from rag.embeddings import _load, embed_one
from rag.indexer import build_index
from rag import seed_corpus
from rag.hybrid_search import DENSE_REJECT_COSINE

model = _load()
build_index()

docs = seed_corpus.all_texts()
texts = [d["text"] for d in docs]
vec_norm = model.encode(texts, normalize_embeddings=True)
vec_raw = model.encode(texts, normalize_embeddings=False)

queries = [
    ("NVDA 毛利率", True),
    ("AI 芯片市场份额", True),
    ("苹果非洲销量", False),
    ("中午吃什么", False),
]

print(f"阈值 DENSE_REJECT_COSINE = {DENSE_REJECT_COSINE}")
print(f"query{'期望':<8}{'余弦(不变)':<14}{'归一化dot':<14}{'未归一化dot':<16}{'误判'}")
print("-" * 70)

for q, should_pass in queries:
    q_norm = embed_one(q)  # 归一化（模长=1）
    q_raw = model.encode([q], normalize_embeddings=False)[0]

    # cosine 值（两种算法都一样，尺度不变）
    cos_best = 0.0
    for vn, vr in zip(vec_norm, vec_raw):
        c = sum(x * y for x, y in zip(q_norm, vn))  # 两边归一 → 点积=cosine
        cos_best = max(cos_best, c)

    # 归一化 dot == cosine（模长=1）
    dot_norm_best = 0.0
    for vn in vec_norm:
        dot_norm_best = max(dot_norm_best, sum(x * y for x, y in zip(q_norm, vn)))

    # 未归一化 dot = |q|·|v|·cosine（被模长放大）
    dot_raw_best = 0.0
    for vr in vec_raw:
        dot_raw_best = max(dot_raw_best, sum(x * y for x, y in zip(q_raw, vr)))

    # 模长参考
    q_raw_mag = math.sqrt(sum(x * x for x in q_raw))

    # 误判判定
    norm_mis = (cos_best < DENSE_REJECT_COSINE) != should_pass
    raw_mis = (dot_raw_best < DENSE_REJECT_COSINE) != should_pass  # 用原始 dot 判

    flag = ""
    if raw_mis and not norm_mis:
        flag = "⚠ 未归一化dot误判"
    elif norm_mis and not raw_mis:
        flag = "⚠ 归一化dot误判"

    print(f"{q:<14}{'放行' if should_pass else '拒答':<8}"
          f"{cos_best:<14.3f}{dot_norm_best:<14.3f}{dot_raw_best:<16.3f}{flag}")

print()
print(f"→ 未归一化 query 模长 |q|≈{q_raw_mag:.1f}，文档 |v| 各不同")
print(f"→ 未归一化 dot 被模长放大 50+ 倍，全部远超 0.55 → 阈值失效")
print(f"→ 归一化后 dot==cosine（有界 0~1），0.55 才有意义")

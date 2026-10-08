"""Day 3 端到端验收：正样本 + 负样本 各跑一次。"""
import sys, json
sys.path.insert(0, ".")

from agents.retrieval import run_retrieval, ensure_rag_ready

ensure_rag_ready()

print("=" * 60)
print("CASE 1 (正样本): NVDA 毛利率，期望带 [n] 引用")
print("=" * 60)
r1 = run_retrieval("NVIDIA 最近一个季度的毛利率是多少", ticker="NVDA")
print("REFUSED:", r1["refused"])
print("ANSWER:\n" + r1["answer"])

print()
print("=" * 60)
print("CASE 2 (负样本): 库内无对应主题，期望拒答")
print("=" * 60)
r2 = run_retrieval("某冷门 ST 股票今天的涨停原因", ticker="")
print("REFUSED:", r2["refused"])
print("ANSWER:\n" + r2["answer"])

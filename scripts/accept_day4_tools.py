"""Day 4 工具层验收：重试 + 降级（不调 LLM，只看数据链路行为）。

用例：
1. get_stock_quote("NVDA") → 能通就 live，不通就 snapshot_fallback + warning
2. get_stock_quote("XXXXXX")（不存在的 ticker）→ 实时和快照都没有 → unavailable
观察 source / warning 字段是否如实反映数据状态。
"""
import sys, json, time
sys.path.insert(0, ".")

from core.tools import finance

print("=" * 56)
print("CASE 1: NVDA 行情（预期 live 或 降级快照 + warning）")
print("=" * 56)
t0 = time.time()
r1 = finance.get_stock_quote("NVDA")
print(f"elapsed={time.time()-t0:.1f}s  source={r1.get('source')}")
print(json.dumps(r1, ensure_ascii=False, indent=2, default=str))

print()
print("=" * 56)
print("CASE 2: 不存在的 ticker（预期 unavailable）")
print("=" * 56)
r2 = finance.get_stock_quote("ZZZZ99")
print(f"source={r2.get('source')}")
print(json.dumps(r2, ensure_ascii=False, indent=2, default=str))

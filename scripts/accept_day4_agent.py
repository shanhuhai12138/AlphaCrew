"""Day 4 Agent 验收：Data Agent 调工具拉 NVDA 数据。

会花 LLM token + 每个工具调用 ~22s（Yahoo 不通走降级），总耗时约 2-5 分钟。
"""
import sys, json
sys.path.insert(0, ".")

from agents.data import run_data

print("跑 Data Agent 验收（NVDA all）...")
r = run_data("NVDA", scope="all")
print(json.dumps(r, ensure_ascii=False, indent=2, default=str))

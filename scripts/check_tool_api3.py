"""查看 structured_tool 与 tool 装饰器的签名/形态。"""
import sys, inspect
sys.path.insert(0, ".")
import crewai.tools as t

st = t.structured_tool
print("structured_tool type:", type(st))
try:
    print("structured_tool sig:", inspect.signature(st))
except Exception as e:
    print("no sig:", e)
print("\nstructured_tool doc:\n", (st.__doc__ or "")[:800])

print("\n===== @tool =====")
print("tool type:", type(t.tool))
try:
    print("tool sig:", inspect.signature(t.tool))
except Exception as e:
    print("no sig:", e)
print("tool doc:\n", (t.tool.__doc__ or "")[:600])

# 顺便看 BaseTool 需要实现什么
from crewai.tools import BaseTool
print("\nBaseTool abstract methods:", [m for m in dir(BaseTool) if not m.startswith('_')])

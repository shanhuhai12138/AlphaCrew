"""检查 CrewAI 1.15 中工具封装的正确导入路径。"""
import sys
sys.path.insert(0, ".")

candidates = [
    ("crewai.tools.tool_builders.simple_tool", "crewai.tools.tool_builders", "simple_tool"),
    ("crewai.tools.simple_tool", "crewai.tools", "simple_tool"),
    ("crewai.tools.FunctionTool", "crewai.tools", "FunctionTool"),
]
for label, mod, attr in candidates:
    try:
        m = __import__(mod, fromlist=[attr])
        fn = getattr(m, attr)
        print(f"OK   {label}")
    except Exception as e:
        print(f"FAIL {label}: {type(e).__name__}: {e}")

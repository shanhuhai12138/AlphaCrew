"""探查 CrewAI 1.15 的工具 API 真实形态。"""
import sys
sys.path.insert(0, ".")
import crewai.tools as t
print("crewai.tools __all__:", getattr(t, "__all__", None))
print("attrs:", [a for a in dir(t) if not a.startswith("_")])
import crewai
print("\ncrewai top-level tool-related:", [a for a in dir(crewai) if "tool" in a.lower()])

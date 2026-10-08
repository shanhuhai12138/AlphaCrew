"""导入冒烟：验证 @tool 封装 + Agent 构建（不建索引、不花 token）。"""
import sys
sys.path.insert(0, ".")

from agents.retrieval import retrieve_financial_evidence, build_retrieval_agent

# 1. 工具对象本身
print("tool name:", retrieve_financial_evidence.name)
print("tool desc head:", (retrieve_financial_evidence.description or "")[:80])

# 2. 工具能不能被 Agent 接受（不执行，只构建）
agent = build_retrieval_agent()
print("agent role:", agent.role)
print("agent tools:", [t.name for t in agent.tools])
print("IMPORT SMOKE OK")

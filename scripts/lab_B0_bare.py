"""最简幻觉演示：一个"没有任何工具"的 Agent，问它 NVDA 毛利率。

它只能靠训练时的记忆"凭印象"回答 → 大概率编一个具体数字，且无来源。
这就是"没有工具兜底时 LLM 的幻觉"。零依赖（不需要 Qdrant / RAG）。
"""
import sys
sys.path.insert(0, ".")
from crewai import Agent, Task, Crew, Process
from core.llm.llm_router import get_llm

Q = "NVIDIA 最近一个季度的毛利率是多少？请给出具体数字。"

bare = Agent(
    role="金融研究员",
    goal="回答用户关于公司财务的问题",
    backstory="你是一名研究员，回答财务问题。",
    llm=get_llm(),
    tools=[],            # ← 关键：不给任何工具，只能靠自身记忆
    verbose=False,
)
task = Task(description=f"用户问题：{Q}", expected_output="简短答案", agent=bare)
r = Crew(agents=[bare], tasks=[task], process=Process.sequential).kickoff()
print("【无工具 Agent 的回答】（只能靠记忆，注意它会不会编一个数字）\n")
print(r.raw or "(空)")

"""幻觉露馅版：问一个"超出 LLM 知识截止"的问题，看它如何编。

问题特意选 2026 年（大概率在训练数据之后）的"最新季度毛利率"。
无工具 Agent 只能靠记忆 → 要么硬编一个带精确小数+日期的数字（最危险），
要么含糊其辞。两种都说明"没有工具/检索兜底时，答案不可信"。
"""
import sys
sys.path.insert(0, ".")
from crewai import Agent, Task, Crew, Process
from core.llm.llm_router import get_llm

Q = "NVIDIA 在 2026 年第二季度（最新一个季度）的毛利率具体是多少？请给出精确数字。"

bare = Agent(
    role="金融研究员",
    goal="回答用户关于公司财务的问题",
    backstory="你是一名研究员，回答财务问题。",
    llm=get_llm(),
    tools=[],
    verbose=False,
)
task = Task(description=f"用户问题：{Q}", expected_output="简短答案", agent=bare)
r = Crew(agents=[bare], tasks=[task], process=Process.sequential).kickoff()
print("【无工具 Agent 回答 2026Q2 毛利率】\n")
print(r.raw or "(空)")
print("\n-> 看它敢不敢直接给一个精确数字。若给了，那不是检索来的，是编的。")

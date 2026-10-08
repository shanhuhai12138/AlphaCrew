"""破坏实验 B：没有工具说明书 / 没有工具时，LLM 会不会编造。

对照两组（都问同一个问题："NVDA 最近一个季度毛利率"）：
  ① 正常 Retrieval Agent：有 @tool 工具 + docstring + task 指令
     → 期望：调工具、拿证据、带 [n] 引用、不编造
  ② 裸 Agent（tools=[]，没任何检索能力）：只靠 LLM 自身参数记忆
     → 期望：直接"凭印象"答一个毛利率数字，无任何来源 → 这就是幻觉

跑完对照，你就"看见"了：幻觉不是抽象概念，是"没有工具兜底时 LLM 拿记忆硬答"。
"""
import sys, json
sys.path.insert(0, ".")

from crewai import Agent, Task, Crew, Process
from core.llm.llm_router import get_llm
from agents.retrieval import run_retrieval, ensure_rag_ready

Q = "NVIDIA 最近一个季度的毛利率是多少"

print("=" * 64)
print("① 正常 Retrieval Agent（有工具 + 说明书）")
print("=" * 64)
ensure_rag_ready()
r1 = run_retrieval(Q, ticker="NVDA")
print("REFUSED:", r1["refused"])
print("ANSWER:\n" + r1["answer"])

print()
print("=" * 64)
print("② 裸 Agent（无工具，纯 LLM 记忆）")
print("=" * 64)
llm = get_llm()
bare = Agent(
    role="金融研究员",
    goal="回答用户关于公司财务的问题",
    backstory="你是一名研究员，回答财务问题。",
    llm=llm,
    tools=[],          # ← 关键：不给任何工具
    verbose=False,
)
task = Task(description=f"用户问题：{Q}", expected_output="简短答案", agent=bare)
r2 = Crew(agents=[bare], tasks=[task], process=Process.sequential).kickoff()
print("ANSWER:\n" + (r2.raw or ""))

print()
print("=" * 64)
print("对照结论：① 带引用/拒答（可信），② 凭记忆编数字（幻觉源）")
print("=" * 64)

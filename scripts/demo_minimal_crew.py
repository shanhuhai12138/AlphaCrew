"""Day 1 验收 demo — 最小 Crew：2 个 Agent 协作生成一段 NVDA 快评。

跑法：
    cd alphacrew
    python scripts/demo_minimal_crew.py

验收标准：
    1. LLM 路由正确解析 provider/model（打印路由结果）
    2. Crew 顺序执行 2 个 task（researcher -> writer）
    3. 输出包含结构化结论 + 免责声明（预埋 Guard 意识）
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.llm.llm_router import get_llm, _resolve
from crewai import Agent, Task, Crew, Process
from core.config import settings


def main() -> None:
    # --- 1. 路由验证（不花 token）---
    provider = settings.llm_provider
    model = settings.llm_model
    litellm_model, extra = _resolve(provider, model)
    print(f"[LLM Router] provider={provider} model={model}")
    print(f"[LLM Router] litellm -> {litellm_model}  base_url={extra.get('base_url')}")

    llm = get_llm(provider, model)
    print(f"[LLM Router] crewai.LLM instance: {llm}")

    # --- 2. 最小 Crew ---
    researcher = Agent(
        role="金融数据研究员",
        goal="收集目标公司的基本面事实（业务、财务趋势、行业地位），只陈述事实不评判",
        backstory="你是一名严谨的卖方研究员，所有结论必须有可追溯的事实支撑，"
                  "不确定时明确标注'数据不足'而非编造。",
        llm=llm,
        verbose=True,
    )
    writer = Agent(
        role="研报撰写编辑",
        goal="把研究员的事实整理为 200 字以内的快评，并附免责声明",
        backstory="你是资深财经编辑，擅长把数据转译为普通人可读的短评，"
                  "绝不把'可能'写成'一定'。",
        llm=llm,
        verbose=True,
    )

    research_task = Task(
        description=(
            "收集 NVIDIA (NVDA) 当前季度的基本面快评素材：主营业务构成、"
            "最近财报的营收/毛利率趋势、AI 芯片市场份额地位。"
            "若数据无法核实，写'数据不足'。"
            "（提示：你看到的 researcher 输出在上方）"
        ),
        expected_output="一段 300 字内的纯事实陈述，含数据点",
        agent=researcher,
    )
    write_task = Task(
        description="基于研究员的事实，写一段 200 字内的中文快评，结尾必须附"
                    "'以上内容仅供参考，不构成投资建议'。",
        expected_output="快评 + 免责声明",
        agent=writer,
         # DAG：writer 依赖 researcher 的输出
    )

    crew = Crew(
        agents=[researcher, writer],
        tasks=[research_task, write_task],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff(inputs={"ticker": "NVDA"})
    print("\n===== FINAL OUTPUT =====")
    print(result.raw if hasattr(result, "raw") else result)


if __name__ == "__main__":
    main()

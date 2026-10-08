"""Day 3 — Retrieval Agent：把 Day 2 的混合检索包成 CrewAI Tool + Agent。

考点：Tool Calling 闭环。
- Agent 自己不会检索，它"拥有"一个工具 retrieve_financial_evidence
- 执行 Task 时 LLM 决定何时调工具、传什么参数（query/ticker/top_k）
- 工具返回带引用的证据文本（正常）或拒答信号（cosine 不足）
- Agent 基于工具结果作答，[n] 引用可回溯；拒答时不得编造

CrewAI 1.15 API 备忘：
- 工具用 @tool 装饰器（crewai.tools.tool），docstring 喂给 LLM 当工具描述
- @tool(result_schema=PydanticModel) 可约束工具输出结构（结构化工具调用考点）
- 旧版 simple_tool / FunctionTool 在 1.15 已不存在
"""
from __future__ import annotations

import json
import logging

from crewai import Agent, Task, Crew, Process
from crewai.tools import tool

from core.llm.llm_router import get_llm
from rag import hybrid_search
from rag.indexer import build_index

logger = logging.getLogger(__name__)

_rag_ready = False


def ensure_rag_ready() -> None:
    """幂等：首次调用时建索引（Qdrant + BM25 内存态）。"""
    global _rag_ready
    if not _rag_ready:
        build_index()
        _rag_ready = True


@tool
def retrieve_financial_evidence(query: str, ticker: str = "", top_k: int = 5) -> str:
    """检索金融语料库，返回带引用编号的证据片段。

    何时使用：回答任何涉及公司基本面/财务/技术面/行业/风险的事实性问题之前，
    必须先调用本工具获取可追溯证据。
    若返回以【拒答信号】开头，表示知识库中无相关证据，必须告知用户"信息不足"，
    严禁基于模型自身记忆编造答案。

    Args:
        query: 要检索的问题或关键词（自然语言，中文即可）
        ticker: 公司代码过滤（如 "NVDA"/"MSFT"/"AMD"）。
                行业/宏观类查询请传空字符串（行业语料不做 ticker 过滤）。
        top_k: 返回的证据片段数（默认 5，最多取 8）
    """
    ensure_rag_ready()
    k = max(1, min(int(top_k), 8))
    result = hybrid_search.hybrid_search(query=query, top_k=k, ticker=ticker or None)
    if result["should_refuse"]:
        logger.info("[RAG Tool] refuse: %s", result["refuse_reason"])
        return (
            "【拒答信号】" + str(result["refuse_reason"])
            + "。知识库中没有与该问题语义对应的证据。"
            "请明确告知用户'当前知识库中没有相关资料，信息不足'，"
            "禁止基于模型自身记忆编造答案。"
        )
    return hybrid_search.format_context(result, max_docs=k)


def build_retrieval_agent(llm=None) -> Agent:
    """检索 Agent：只负责'查证据'，不写报告。"""
    llm = llm or get_llm()
    return Agent(
        role="证据检索专员",
        goal="为用户的问题检索语料库中可追溯的证据片段，并如实标注来源；"
             "证据不足时明确声明'信息不足'，绝不编造",
        backstory="你是一名严谨的研究助理，只用检索工具获得证据后再作答，"
                  "每个论断必须用 [n] 指回工具返回的片段编号。"
                  "当工具返回【拒答信号】时，直接回答'当前知识库中无相关资料，信息不足'。",
        llm=llm,
        tools=[retrieve_financial_evidence],
        verbose=False,
    )


def run_retrieval(query: str, ticker: str = "", top_k: int = 5) -> dict:
    """单 Agent 验收入口：query → Agent 调工具 → 带引用答案。

    返回 {"answer": str, "refused": bool}
    """
    ensure_rag_ready()
    agent = build_retrieval_agent()
    task = Task(
        description=(
            f"用户问题：{query}\n"
            f"（公司代码过滤：{ticker or '无/行业类'}）\n"
            f"请先调用 retrieve_financial_evidence 工具检索证据（top_k={top_k}）再作答；"
            "每个论断用 [n] 引用工具返回的片段编号。"
        ),
        expected_output="带 [n] 引用标注的简短答案；若无证据则回答'当前知识库中没有相关资料，信息不足'",
        agent=agent,
    )
    result = Crew(
        agents=[agent], tasks=[task], process=Process.sequential
    ).kickoff()
    answer = result.raw or ""
    refused = "拒答信号" in answer or "信息不足" in answer
    return {"answer": answer, "refused": refused}


if __name__ == "__main__":
    # 快速自测（需要 Qdrant 已启动 + .env 有 LLM key）
    r = run_retrieval("NVIDIA 最近一个季度的毛利率是多少", ticker="NVDA")
    print(json.dumps(r, ensure_ascii=False, indent=2))

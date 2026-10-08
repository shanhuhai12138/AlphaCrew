"""Day 4 — Data Agent：会调外部金融 API 拉实时数据的 Agent。

考点：多工具 Tool Calling + 优雅降级。
- Agent 拥有 4 个工具（get_stock_quote / get_financials / get_technicals / get_all_for）
- 执行 Task 时 LLM 自主决定调哪个工具、传哪个 ticker
- 工具内部已实现"实时不可达 → 降级快照 + warning 标注"，
  Agent 拿到带 warning 的数据后，必须在答案里如实告知用户"非实时数据"
- 这是 Day 3（查自己的库）的进阶：Day 3 是受控 RAG，Day 4 是开放世界 API
"""
from __future__ import annotations

import json
import logging

from crewai import Agent, Task, Crew, Process
from crewai.tools import tool

from core.llm.llm_router import get_llm
from core.tools import finance

logger = logging.getLogger(__name__)


@tool
def get_stock_quote(ticker: str) -> dict:
    """获取股票实时行情：最新价、涨跌幅、市值。

    Args:
        ticker: 股票代码（如 "NVDA"）。
    返回值含 source 字段：yahoo_finance_live=实时；snapshot_fallback=内置快照（带
    warning，数据非实时）；unavailable=无数据。若 source 非 live，答案中必须说明。
    """
    return finance.get_stock_quote(ticker)


@tool
def get_financials(ticker: str) -> dict:
    """获取公司财报摘要：营收、增速、毛利率等财务指标。

    Args:
        ticker: 股票代码。
    source 字段含义同 get_stock_quote；非 live 时须标注数据时效性。
    """
    return finance.get_financials(ticker)


@tool
def get_technicals(ticker: str) -> dict:
    """获取技术指标：52 周区间、市盈率、beta、股息率。

    Args:
        ticker: 股票代码。
    """
    return finance.get_technicals(ticker)


@tool
def get_all_for(ticker: str) -> dict:
    """一次性获取某股票的全部数据（行情 + 财报 + 技术指标）。

    当任务需要综合多类数据时优先用本工具，减少调用次数。

    Args:
        ticker: 股票代码。
    """
    return finance.get_all_for(ticker)


def build_data_agent(llm=None) -> Agent:
    """数据 Agent：负责拉取结构化金融数据，不写报告。"""
    llm = llm or get_llm()
    return Agent(
        role="金融数据工程师",
        goal="为下游分析提供准确、标注了来源与时效性的结构化金融数据",
        backstory="你是一名数据工程师，只用提供的工具获取数据，绝不凭空编造数字。"
                  "当工具返回 source 为 snapshot_fallback 或含 warning 时，"
                  "必须在输出中明确标注'此为快照数据，非实时'。",
        llm=llm,
        tools=[get_stock_quote, get_financials, get_technicals, get_all_for],
        verbose=False,
    )


def run_data(ticker: str, scope: str = "all") -> dict:
    """Data Agent 验收入口：ticker → Agent 调工具 → 结构化数据。

    scope: "quote"/"financials"/"technicals"/"all"
    """
    agent = build_data_agent()
    scope_map = {
        "quote": "调用 get_stock_quote 获取行情",
        "financials": "调用 get_financials 获取财报",
        "technicals": "调用 get_technicals 获取技术指标",
        "all": "调用 get_all_for 获取全部数据",
    }
    task = Task(
        description=f"目标股票 {ticker.upper()}：{scope_map.get(scope, scope_map['all'])}。"
                    f"获取后以 JSON 输出，并保留 source/warning 字段。",
        expected_output="结构化 JSON（含 source 与时效性标注）",
        agent=agent,
    )
    result = Crew(
        agents=[agent], tasks=[task], process=Process.sequential
    ).kickoff()
    return {"ticker": ticker.upper(), "output": result.raw or ""}


if __name__ == "__main__":
    r = run_data("NVDA", scope="all")
    print(json.dumps(r, ensure_ascii=False, indent=2))

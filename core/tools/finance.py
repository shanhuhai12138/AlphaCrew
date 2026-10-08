"""金融数据工具层 — Yahoo Finance 实时数据 + 内置快照降级。

设计考点（面试可直接讲）：
1. 多工具编排：3 个工具（行情/财报/技术指标）供 Data Agent 自主调用
2. 指数退避重试：transient error 重试 3 次（0.5s/1s/2s），final 失败上抛
3. 超时控制：单次请求 10s，避免一个慢 API 拖垮整个 Agent 流程
4. 优雅降级：所有重试失败 → 返回内置快照数据（source=SNAPSHOT，明确标注
   "数据时效性未知"），Agent 流程不中断，答案不编造
5. 静态快照兜底数据：来自 seed_corpus 的 FY2025 数字，离线可跑通 demo
"""
from __future__ import annotations

import time
from typing import Any, Callable

import requests

# ---------- 内置快照（降级兜底，数字与 rag/seed_corpus.py 保持一致）----------
SNAPSHOT: dict[str, dict[str, Any]] = {
    "NVDA": {
        "quote": {"price": 138.29, "change_pct": 2.1, "market_cap_b_usd": 3.42,
                  "note": "示例快照价（非实时）"},
        "financials": {"fy2025_revenue_b_usd": 130.5, "fy2025_growth_pct": 114,
                       "q4_revenue_b_usd": 39.3, "q4_gross_margin_pct": 73,
                       "datacenter_share_pct": 88},
        "technicals": {"52w_range": [86.62, 151.41], "trailing_pe": 45.3,
                       "beta": 1.7, "dividend_yield_pct": 0.02},
    },
    "MSFT": {
        "quote": {"price": 448.50, "change_pct": 0.8, "market_cap_b_usd": 3.38,
                  "note": "示例快照价（非实时）"},
        "financials": {"operating_margin_pct": 45, "note": "FY2025 现金牛属性"},
        "technicals": {"trailing_pe": 32.1, "beta": 1.1},
    },
    "AMD": {
        "quote": {"price": 132.4, "change_pct": 1.4, "market_cap_b_usd": 0.195,
                  "note": "示例快照价（非实时）"},
        "financials": {"note": "数据中心第二增长曲线（EPYC + MI300）"},
        "technicals": {"trailing_pe": 95.0, "beta": 1.5},
    },
}

TIMEOUT_SEC = 10
MAX_RETRIES = 3
BACKOFF_BASE = 0.5  # 0.5s → 1s → 2s


def _with_retry(fn: Callable[[], dict]) -> dict:
    """指数退避重试；全失败抛 RuntimeError（由调用方决定降级策略）。"""
    last_exc: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001 - 网络层全量捕获
            last_exc = e
            time.sleep(BACKOFF_BASE * (2 ** attempt))
    raise RuntimeError(f"重试 {MAX_RETRIES} 次后仍失败: {last_exc}")


def get_stock_quote(ticker: str) -> dict:
    """实时行情：价格/涨跌幅/市值。失败自动降级到内置快照。"""
    ticker = ticker.upper()
    try:
        def _call() -> dict:
            url = (f"https://query1.finance.yahoo.com/v7/finance/quote"
                   f"?symbols={ticker}")
            r = requests.get(url, timeout=TIMEOUT_SEC,
                             headers={"User-Agent": "Mozilla/5.0 (AlphaCrew)"})
            r.raise_for_status()
            items = r.json().get("quoteResponse", {}).get("result", [])
            if not items:
                raise ValueError(f"Yahoo 未返回 {ticker}")
            q = items[0]
            return {
                "ticker": ticker,
                "price": q.get("regularMarketPrice"),
                "change_pct": q.get("regularMarketChangePercent"),
                "market_cap": q.get("marketCap"),
                "source": "yahoo_finance_live",
                "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        return _with_retry(_call)
    except Exception as e:  # noqa: BLE001
        snap = SNAPSHOT.get(ticker)
        if snap:
            return {**snap["quote"], "ticker": ticker,
                    "source": "snapshot_fallback",
                    "warning": f"实时接口不可达（{type(e).__name__}），已降级为内置快照，数据时效性未知"}
        return {"ticker": ticker, "source": "unavailable",
                "warning": f"实时接口不可达且无快照兜底：{e}"}


def get_financials(ticker: str) -> dict:
    """财报摘要：营收/增速/毛利率。失败降级快照。"""
    ticker = ticker.upper()
    try:
        def _call() -> dict:
            url = ("https://query1.finance.yahoo.com/v10/finance/quoteSummary/"
                   f"{ticker}?modules=incomeStatementHistory,defaults")
            r = requests.get(url, timeout=TIMEOUT_SEC,
                             headers={"User-Agent": "Mozilla/5.0 (AlphaCrew)"})
            r.raise_for_status()
            data = r.json().get("quoteSummary", {}).get("result", [{}])[0]
            return {"ticker": ticker, "raw": data, "source": "yahoo_finance_live"}
        return _with_retry(_call)
    except Exception as e:  # noqa: BLE001
        snap = SNAPSHOT.get(ticker)
        if snap:
            return {**snap["financials"], "ticker": ticker,
                    "source": "snapshot_fallback",
                    "warning": f"实时接口不可达（{type(e).__name__}），已降级为内置快照"}
        return {"ticker": ticker, "source": "unavailable", "warning": str(e)}


def get_technicals(ticker: str) -> dict:
    """技术指标：52 周区间/PE/beta。失败降级快照。"""
    ticker = ticker.upper()
    try:
        def _call() -> dict:
            url = ("https://query1.finance.yahoo.com/v10/finance/quoteSummary/"
                   f"{ticker}?modules=price,summaryDetail")
            r = requests.get(url, timeout=TIMEOUT_SEC,
                             headers={"User-Agent": "Mozilla/5.0 (AlphaCrew)"})
            r.raise_for_status()
            data = r.json().get("quoteSummary", {}).get("result", [{}])[0]
            return {"ticker": ticker, "raw": data, "source": "yahoo_finance_live"}
        return _with_retry(_call)
    except Exception as e:  # noqa: BLE001
        snap = SNAPSHOT.get(ticker)
        if snap and "technicals" in snap:
            return {**snap["technicals"], "ticker": ticker,
                    "source": "snapshot_fallback",
                    "warning": f"实时接口不可达（{type(e).__name__}），已降级为内置快照"}
        return {"ticker": ticker, "source": "unavailable", "warning": str(e)}


def get_all_for(ticker: str) -> dict:
    """一次拿全：行情 + 财报 + 技术指标（Agent 常用入口）。"""
    return {
        "quote": get_stock_quote(ticker),
        "financials": get_financials(ticker),
        "technicals": get_technicals(ticker),
    }

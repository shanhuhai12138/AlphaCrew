"""金融语料 — 内置结构化文档片段（Day 2 用种子语料跑通链路）。

每篇文档带 source（来源）+ ticker + section，供引用溯源用。
Day 2 阶段先内置 ~24 条覆盖 NVDA/MSFT/AMD/行业/风险的片段；
Day 7 之后可换成爬取的真实研报 + 10-K 摘要扩充。

面试考点：分块策略 —— 这里按"文档-段落"粒度预切，保留
metadata（ticker/section/source），检索时可做"按 ticker 过滤"。
"""
from __future__ import annotations

# 每条: {id, text, ticker, section, source}
CORPUS: list[dict] = [
    # ===== NVDA =====
    {"id": "nvda-01", "ticker": "NVDA", "section": "基本面", "source": "NVIDIA FY2025 年报",
     "text": "NVIDIA 主营业务分数据中心、游戏、专业可视化、汽车四大板块。FY2025 全年营收约 1305 亿美元，同比增长 114%，其中数据中心全年营收约 1152 亿美元，占总营收约 88%。"},
    {"id": "nvda-02", "ticker": "NVDA", "section": "财务", "source": "NVIDIA FY2025 Q4 财报",
     "text": "NVIDIA FY2025 第四季度单季营收约 393 亿美元，同比增长 78%；全年 GAAP 毛利率约 75%，Q4 毛利率约 73%，公司归因于 Blackwell 新品爬坡成本。"},
    {"id": "nvda-03", "ticker": "NVDA", "section": "技术面", "source": "NVIDIA 产品路线图",
     "text": "NVIDIA 数据中心 GPU 采用 Ampere → Hopper（H100/H200）→ Blackwell（B200）→ Rubin 的迭代节奏，Blackwell 主打 NVLink 域扩展与 FP8/FP4 低精度推理，面向大模型训练与推理双场景。"},
    {"id": "nvda-04", "ticker": "NVDA", "section": "行业", "source": "IDC / TrendForce 行业口径（估算）",
     "text": "第三方机构（IDC、TrendForce）估算 NVIDIA 在数据中心 AI 加速芯片市场占有率约 80%–90%，但口径差异大，精确季度份额数据不足。"},
    {"id": "nvda-05", "ticker": "NVDA", "section": "风险", "source": "行业分析",
     "text": "NVIDIA 风险点：一是 AI 加速器客户集中（头部云厂商占比较高），二是出口管制对部分区域销售的影响，三是自研 ASIC（如云厂自研芯片）对通用 GPU 的长期替代压力。"},

    # ===== MSFT =====
    {"id": "msft-01", "ticker": "MSFT", "section": "基本面", "source": "Microsoft FY2025 10-K 摘要",
     "text": "Microsoft 三大分部为生产力与商业、智能云、更多商业。智能云包含 Azure，是 AI 算力服务的主力；Copilot 产品线覆盖 Office、Windows、DevOps 全栈。"},
    {"id": "msft-02", "ticker": "MSFT", "section": "财务", "source": "Microsoft FY2025 财报",
     "text": "Microsoft 智能云收入持续增长，Azure 同比增速在 AI 需求拉动下高于历史均值；营业利润率约 45%，现金牛属性强，回购规模大。"},
    {"id": "msft-03", "ticker": "MSFT", "section": "技术面", "source": "Azure 技术公告",
     "text": "Microsoft 与 OpenAI 深度合作，Azure 提供 H100/H200 及自研 Maia 芯片；Copilot 基于 GPT 系列模型，按席位订阅收费，是企业级 AI 商业化主力。"},
    {"id": "msft-04", "ticker": "MSFT", "section": "风险", "source": "行业分析",
     "text": "Microsoft 风险点：AI 资本开支高企影响短期自由现金流；企业客户对 Copilot 付费转化率的可持续性存疑；反垄断监管对收购与生态的限制。"},

    # ===== AMD =====
    {"id": "amd-01", "ticker": "AMD", "section": "基本面", "source": "AMD 2024 年报摘要",
     "text": "AMD 数据中心业务（EPYC 服务器 CPU + Instinct MI300 系列 GPU）是第二增长曲线，与 NVIDIA 在 AI 加速器市场直接竞争，MI300X 主打性价比与开放 ROCm 生态。"},
    {"id": "amd-02", "ticker": "AMD", "section": "技术面", "source": "AMD 产品公告",
     "text": "AMD Instinct MI300/MI325 采用 CDNA 架构，主打大显存（192/256GB HBM3e）降低大模型推理成本；软件栈 ROCm 对 CUDA 生态的兼容是主要短板。"},
    {"id": "amd-03", "ticker": "AMD", "section": "风险", "source": "行业分析",
     "text": "AMD 风险点：GPU 软件生态（ROCm vs CUDA）成熟度差距导致大模型开发者优先选 NVIDIA；数据中心 GPU 份额仍显著低于 NVIDIA；消费级游戏 CPU 竞争激烈。"},

    # ===== 行业 / 宏观 =====
    {"id": "industry-01", "ticker": "INDUSTRY", "section": "行业", "source": "行业研报综述",
     "text": "AI 算力需求进入结构性扩张期：大模型训练参数规模与推理调用量双升，数据中心资本开支（hyperscaler capex）是 GPU 需求的核心先行指标。"},
    {"id": "industry-02", "ticker": "INDUSTRY", "section": "行业", "source": "行业研报综述",
     "text": "推理侧成本与能效成为 2025 年竞争焦点：FP8/FP4 低精度量化、超大显存、NVLink/Infinity Fabric 互联决定单卡可承载的模型规模，芯片厂商纷纷推推理优化产品线。"},
    {"id": "industry-03", "ticker": "INDUSTRY", "section": "宏观", "source": "宏观数据（BLS/Bea）",
     "text": "宏观角度：高利率环境约束企业资本开支与估值；美国 hyperscaler（MSFT/GOOG/AMZN）的年度 AI capex 指引是观察算力需求最直接的公开指标。"},
    {"id": "industry-04", "ticker": "INDUSTRY", "section": "行业", "source": "行业研报综述",
     "text": "供应链侧：HBM（高带宽内存）与先进封装（CoWoS）是 AI 芯片的关键瓶颈，HBM 产能与 NVIDIA/AMD 出货强相关，是观察算力景气度的上游指标。"},

    # ===== 风险专项 =====
    {"id": "risk-01", "ticker": "NVDA", "section": "风险", "source": "监管与政策",
     "text": "出口管制风险：美国对部分地区的 AI 芯片出口限制可能影响 NVIDIA 区域收入结构，公司需通过降规产品（如 H20）维持市场，但削弱高毛利芯片占比。"},
    {"id": "risk-02", "ticker": "INDUSTRY", "section": "风险", "source": "行业分析",
     "text": "行业共性风险：AI 资本开支若不及预期，GPU 厂商收入弹性将直接下修；同时自研 ASIC 渗透率上升会侵蚀通用 GPU 的长期份额。"},

    # ===== 评测用负样本（测试拒答/低相关识别）=====
    {"id": "neg-01", "ticker": "AAPL", "section": "基本面", "source": "Apple 2024 财报摘要",
     "text": "Apple 以 iPhone、服务与可穿戴设备为核心，收入结构以消费硬件为主，与 AI 算力芯片赛道关联度低。"},
    {"id": "neg-02", "ticker": "INDUSTRY", "section": "历史", "source": "半导体史",
     "text": "2008 年智能手机爆发带动移动端 SoC 需求，是上一轮半导体上行周期，与当前 AI 算力周期驱动逻辑不同。"},
]


def all_texts() -> list[dict]:
    return list(CORPUS)


def count() -> int:
    return len(CORPUS)

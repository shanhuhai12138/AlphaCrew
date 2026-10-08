# AlphaCrew 架构设计

> 多 Agent 金融研报生成器 — 基于 CrewAI 1.15 二次开发
> 与 KnowledgeFlow-AI 的差异化：KF = 单 Agent 线性工作流 + 用户文档 RAG；AlphaCrew = 多 Agent 自主协作 + 外部数据获取 + 深度规划 + 评估 + 安全对齐。

## 模块地图（每个模块 = 一个面试考点）

```
alphacrew/
├── core/
│   ├── config.py          # 全局配置（pydantic-settings 读 .env）
│   ├── llm/llm_router.py  # 【考点: 多模型接入】OpenAI 兼容协议，用户可自选 Agnes/DeepSeek/OpenAI
│   ├── memory/            # 【考点: Memory 三层】对话级 / 任务级(Redis 黑板) / 长期(Qdrant 跨会话)
│   ├── planning/          # 【考点: ReAct/DAG 规划】ReAct 循环、任务分解、动态重规划
│   └── tools/             # 【考点: Tool Calling】工具注册、MCP 接入、重试/超时/熔断
├── agents/
│   ├── planner.py         # 规划 Agent：拆解研报子任务 → DAG
│   ├── data.py            # 数据 Agent：Tool Calling 拉 Yahoo Finance / Alpha Vantage
│   ├── retrieval.py       # 检索 Agent：混合 RAG（Qdrant 向量 + BM25）
│   ├── analyst.py         # 4× 分析师 Agent（基本面/财务/技术/行业，并行）
│   ├── writer.py          # 写手 Agent：模板化长文生成
│   ├── critic.py          # 审稿 Agent：LLM-as-Judge 忠实度评分
│   └── guard.py           # 守护 Agent：注入检测 + 合规免责声明
├── rag/                   # 【考点: RAG 全链路】分块、嵌入、混合检索、RRF、引用溯源、拒答授权
├── eval/                  # 【考点: 评估】评测集、Recall@K、MRR、幻觉率、CI 门禁
├── guard/                 # 【考点: 安全对齐】输入/输出双向 guardrail
├── observability/         # 【考点: 可观测】Langfuse trace、结构化日志、成本监控
├── backend/               # 【考点: 流式交互】FastAPI + SSE 事件协议
└── frontend/              # 【考点: 前端】Vue 3 + 多 Agent 步骤可视化 DAG
```

## Agent 协作 DAG（研报生成主流程）

```
                    ┌─────────────┐
  用户输入 ticker ──▶│  Guard 输入 │
                    └──────┬──────┘
                           ▼
                    ┌─────────────┐
                    │  Planner    │  拆 5 子任务: 基本面/财务/技术/行业/风险
                    └──────┬──────┘
            ┌───────────┬──┴───────┬────────────┐
            ▼           ▼          ▼            ▼
      ┌──────────┐┌──────────┐┌──────────┐┌──────────┐
      │ 基本面    ││ 财务     ││ 技术     ││ 行业     │   4 个 Analyst 并行
      │ Analyst  ││ Analyst  ││ Analyst  ││ Analyst  │   每个内部: RAG + Data Tool
      └────┬─────┘└────┬─────┘└────┬─────┘└────┬─────┘
            └───────────┴─────┬─────┴───────────┘
                              ▼
                    ┌─────────────┐
                    │   Writer    │  按研报模板分段生成
                    └──────┬──────┘
                           ▼
                    ┌─────────────┐
                    │   Critic    │  逐论断溯源，输出忠实度分数
                    └──────┬──────┘
                           ▼
                    ┌─────────────┐
                    │  Guard 输出 │  免责声明 + 数据时效标注
                    └──────┬──────┘
                           ▼
                     报告交付（SSE 流式）
```

## 技术选型

| 组件 | 选型 | 理由 |
|------|------|------|
| Agent 框架 | CrewAI 1.15 | 角色化 Agent 抽象、内置 Memory/Tool Failure 策略、代码量适中可通读 |
| 向量库 | Qdrant | 与 KF 项目一致，可复用已有经验 |
| 嵌入 | BAAI/bge-small-zh-v1.5（本地）+ 可切 API | 3060 可跑；架构上支持换 API 嵌入 |
| LLM | 用户自选（Agnes/DeepSeek/OpenAI 兼容） | 统一 OpenAI 协议，前端可切换 |
| 任务黑板 | Redis | 与 KF 的 Streams 经验衔接 |
| 后端 | FastAPI + sse-starlette | SSE 事件协议考点 |
| 前端 | Vue 3 + TypeScript + Vite | 复用 KF 前端经验 |
| 可观测 | Langfuse（自托管） | Agent trace 可视化 |

# AlphaCrew — 多 Agent 金融研报生成器

基于 **CrewAI 1.15** 二次开发的多 Agent 协作金融研报系统：用户输入 ticker，系统自动拆解任务、拉取行情数据、混合 RAG 检索、多 Analyst 并行分析、模板化撰写、LLM-as-Judge 审稿、Guard 安全合规审查，SSE 流式交付带引用的研报。

> 与 KnowledgeFlow-AI 的差异化：KF = 单 Agent 线性工作流 + 用户文档 RAG（检索型）；AlphaCrew = 多 Agent 自主协作 + 外部数据获取 + 深度规划（自主型）。

## 架构与面试考点映射

```
alphacrew/
├── core/
│   ├── config.py          # 全局配置（pydantic-settings 读 .env）
│   ├── llm/llm_router.py  # 【多模型接入】OpenAI 兼容协议：Agnes / DeepSeek / OpenAI 用户可自选
│   ├── memory/            # 【Memory 三层】对话级 / 任务级(Redis 黑板) / 长期(Qdrant 跨会话)
│   ├── planning/          # 【ReAct/DAG 规划】任务分解、动态重规划
│   └── tools/             # 【Tool Calling】工具注册、MCP 接入、重试/超时/熔断
├── agents/                # Planner / Data / Retrieval / 4×Analyst / Writer / Critic / Guard
├── rag/                   # 【RAG 全链路】bge-small-zh 嵌入 + Qdrant 向量 + BM25(jieba) 混合检索
│                          #             + RRF 融合 + 引用溯源 + dense-cosine 拒答授权
├── eval/                  # 【评估】评测集、Recall@K、MRR、幻觉率、CI 门禁
├── guard/                 # 【安全对齐】输入注入检测 + 输出合规免责声明
├── observability/         # 【可观测】Langfuse trace、结构化日志
├── backend/               # 【流式交互】FastAPI + SSE 事件协议
└── frontend/              # Vue 3 + 多 Agent 步骤可视化 DAG
```

## 快速开始

```bash
# 1. 依赖
.venv\Scripts\pip install -r requirements.txt

# 2. 配置
copy .env.example .env   # 填入至少一个 LLM key（DeepSeek / Agnes）

# 3. 启动 Qdrant
docker run -d -p 6333:6333 qdrant/qdrant:latest

# 4. 验证
.venv\Scripts\python scripts\verify_rag.py        # RAG 混合检索 + 拒答授权
.venv\Scripts\python scripts\demo_minimal_crew.py # 最小 Crew 协作 demo
```

## RAG 检索质量（种子语料 20 条，实测）

- 混合检索（Dense + BM25 + RRF）相关查询 Recall@5 = 100%，纯向量路约 94%
- 拒答授权：dense top1 cosine < 0.55 自动拒答（阈值经 6 组 query 实测校准）
- 正样本 cosine 分布 0.74–0.83，库内相邻主题 0.62，库内无对应主题 ≤0.54

## 技术选型

| 组件 | 选型 | 理由 |
|------|------|------|
| Agent 框架 | CrewAI 1.15 | 角色化 Agent 抽象、内置 Memory / Tool Failure 策略 |
| 向量库 | Qdrant | payload 过滤 + 向量检索一体化，按 ticker 结构化过滤 |
| 嵌入 | bge-small-zh-v1.5（本地 3060 可跑） | 512 维，架构支持切 API 嵌入 |
| LLM | 用户自选（OpenAI 兼容协议） | 前端可切 Agnes / DeepSeek / OpenAI |
| 后端 | FastAPI + SSE | 流式事件协议考点 |
| 前端 | Vue 3 + TypeScript | 多 Agent DAG 步骤可视化 |
